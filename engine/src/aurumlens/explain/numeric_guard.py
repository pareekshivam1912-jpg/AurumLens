"""Numeric Guard for AurumLens Explainer (Rule R25).

Mandate:
- An explanation must NEVER compute numbers dynamically.
- Every number appearing in the generated explanation text must be present
  in the underlying evidence record JSON.
- If any number is synthesized or hallucinated, the guard fails.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set


class NumericGuardViolationError(Exception):
    """Raised when an explanation contains a number not found in the evidence JSON."""
    pass


def _extract_numbers_from_text(text: str) -> Set[float]:
    """Extract all numbers from text (integers, decimals, currency values)."""
    # Remove Indian currency symbol and commas from rupee groupings: e.g. ₹1,20,500.00 -> 120500.00
    cleaned = text.replace("₹", "").replace(",", "")
    # Find all decimal/integer numbers, optional leading sign
    matches = re.findall(r"[-+]?\d*\.?\d+", cleaned)
    numbers: Set[float] = set()
    for m in matches:
        if m in ("", "-", "+", "."):
            continue
        try:
            val = float(m)
            numbers.add(round(val, 4))
        except ValueError:
            continue
    return numbers


def _extract_numbers_from_evidence(data: Any) -> Set[float]:
    """Recursively collect all numeric values present in the evidence record dictionary."""
    numbers: Set[float] = set()

    if isinstance(data, dict):
        for v in data.values():
            numbers.update(_extract_numbers_from_evidence(v))
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            numbers.update(_extract_numbers_from_evidence(item))
    elif isinstance(data, (int, float)) and not isinstance(data, bool):
        numbers.add(round(float(data), 4))
    elif isinstance(data, str):
        # In case dates or strings have numeric substrings, extract them too
        nums = _extract_numbers_from_text(data)
        numbers.update(nums)

    return numbers


def verify_numeric_guard(text: str, evidence_data: Dict[str, Any], allowed_date_parts: bool = True) -> bool:
    """Verify that every number in `text` exists in `evidence_data`.

    Parameters
    ----------
    text : str
        Generated explanation text in English, Hindi, etc.
    evidence_data : dict
        Evidence record data as a dictionary.
    allowed_date_parts : bool
        If True, common date parts (years, months, days) from trade_date are considered valid.

    Returns
    -------
    bool
        True if all numbers pass the guard, False otherwise.
    """
    text_numbers = _extract_numbers_from_text(text)
    evidence_numbers = _extract_numbers_from_evidence(evidence_data)

    for num in text_numbers:
        # Check direct match with roundoff tolerance
        matched = False
        for ev_num in evidence_numbers:
            if abs(num - ev_num) < 0.005:
                matched = True
                break
        if not matched:
            return False

    return True


def assert_numeric_guard(text: str, evidence_data: Dict[str, Any]) -> None:
    """Assert numeric guard, raising NumericGuardViolationError on failure."""
    if not verify_numeric_guard(text, evidence_data):
        text_numbers = _extract_numbers_from_text(text)
        evidence_numbers = _extract_numbers_from_evidence(evidence_data)
        unmatched = [n for n in text_numbers if not any(abs(n - en) < 0.005 for en in evidence_numbers)]
        raise NumericGuardViolationError(
            f"Numeric guard failed! Numbers not present in evidence JSON: {unmatched}"
        )
