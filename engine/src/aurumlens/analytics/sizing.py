"""Lot-ratio sizing analytics module for AurumLens.

Implements cross-contract lot-ratio sizing per Design §6.7 (R22):
Calculates integer lot quantities (n_A, n_B) that minimize the unhedged
residual fine gold grams between two contracts.

Key formulas:
    - Fine grams per lot:
        g_i = trading_unit_g_i * (purity_i / 0.999)
    - Optimal lot search:
        Search integers 1 <= n_A, n_B <= max_lots_per_leg that minimize
        |n_A * g_A - n_B * g_B|, then smallest notional, subject to max_notional_inr.
    - Residual fine grams:
        residual_fine_g = n_A * g_A - n_B * g_B
        (Positive sign indicates leg A is long gold; negative indicates leg B is long gold).

Key Fixture (from Design.md):
    GOLDTEN (10g, 999) vs GOLDGUINEA (8g, 999):
    Ratio 4 : 5 (40g vs 40g, residual 0).
"""

from dataclasses import dataclass
from typing import Any, Optional, Tuple


@dataclass(frozen=True)
class SizingResult:
    """Result of cross-contract lot-ratio sizing.

    Can be unpacked as a 3-tuple (lots_a, lots_b, residual_fine_g)
    or accessed via named attributes.

    Attributes
    ----------
    lots_a : int
        Number of integer lots for leg A (1 <= lots_a <= max_lots_per_leg).
    lots_b : int
        Number of integer lots for leg B (1 <= lots_b <= max_lots_per_leg).
    residual_fine_g : float
        Unhedged fine grams: n_A * g_A - n_B * g_B.
        Positive sign indicates leg A is net long gold; negative indicates leg B is net long gold.
    fine_grams_a : float
        Total fine grams in leg A: lots_a * g_A.
    fine_grams_b : float
        Total fine grams in leg B: lots_b * g_B.
    notional_a : Optional[float]
        INR notional of leg A if prices are available.
    notional_b : Optional[float]
        INR notional of leg B if prices are available.
    total_notional : Optional[float]
        Combined INR notional (notional_a + notional_b) if prices are available.
    """

    lots_a: int
    lots_b: int
    residual_fine_g: float
    fine_grams_a: float
    fine_grams_b: float
    notional_a: Optional[float] = None
    notional_b: Optional[float] = None
    total_notional: Optional[float] = None

    def __iter__(self):
        """Enable unpacking as (lots_a, lots_b, residual_fine_g)."""
        return iter((self.lots_a, self.lots_b, self.residual_fine_g))

    def __getitem__(self, index: int):
        return (self.lots_a, self.lots_b, self.residual_fine_g)[index]

    def __len__(self) -> int:
        return 3


def fine_grams_per_lot(
    trading_unit_g: float,
    purity: float,
    target_purity: float = 0.999,
) -> float:
    """Calculate the fine gold grams represented by one contract lot.

    Formula per Design §6.7 (R22):
        g_i = trading_unit_g_i * (purity_i / target_purity)

    Parameters
    ----------
    trading_unit_g : float
        Contract trading unit in grams (e.g. 100 for GOLDM, 10 for GOLDTEN, 8 for GOLDGUINEA, 1 for GOLDPETAL).
    purity : float
        Contract fineness (e.g. 0.995 for GOLDM, 0.999 for GOLDTEN).
    target_purity : float, optional
        Standard reference purity (default 0.999).

    Returns
    -------
    float
        Fine grams per lot equivalent.

    Raises
    ------
    ValueError
        If trading_unit_g <= 0, purity <= 0, or target_purity <= 0.
    """
    if trading_unit_g <= 0:
        raise ValueError(f"trading_unit_g must be strictly positive, got {trading_unit_g}")
    if purity <= 0:
        raise ValueError(f"purity must be strictly positive, got {purity}")
    if target_purity <= 0:
        raise ValueError(f"target_purity must be strictly positive, got {target_purity}")

    return trading_unit_g * (purity / target_purity)


def calculate_lot_ratio(
    *args: Any,
    g_a: Optional[float] = None,
    g_b: Optional[float] = None,
    max_lots_per_leg: int = 50,
    max_notional_inr: Optional[float] = 2_500_000.0,
    price_a: Optional[float] = None,
    price_b: Optional[float] = None,
    trading_unit_a: Optional[float] = None,
    purity_a: Optional[float] = None,
    trading_unit_b: Optional[float] = None,
    purity_b: Optional[float] = None,
    target_purity: float = 0.999,
    **kwargs: Any,
) -> SizingResult:
    """Search integer lot quantities (n_A, n_B) minimizing unhedged fine grams.

    Per Design §6.7 (R22):
        1 <= n_A, n_B <= max_lots_per_leg
        Objective 1: minimize |n_A * g_A - n_B * g_B|
        Objective 2 (tie-breaker): smallest notional
        Subject to: max_notional_inr

    Parameters
    ----------
    g_a : float, optional
        Fine grams per lot for leg A.
    g_b : float, optional
        Fine grams per lot for leg B.
    max_lots_per_leg : int, optional
        Upper bound on lots per leg, default 50.
    max_notional_inr : float, optional
        Maximum INR notional per leg, default 2,500,000.0.
    price_a : float, optional
        Price for leg A (normalized price per 10g 999 or quoted price).
    price_b : float, optional
        Price for leg B (normalized price per 10g 999 or quoted price).
    trading_unit_a : float, optional
        Trading unit grams for leg A (if g_a not provided).
    purity_a : float, optional
        Purity for leg A (if g_a not provided).
    trading_unit_b : float, optional
        Trading unit grams for leg B (if g_b not provided).
    purity_b : float, optional
        Purity for leg B (if g_b not provided).
    target_purity : float, optional
        Target reference purity, default 0.999.

    Returns
    -------
    SizingResult
        Object containing lots_a, lots_b, residual_fine_g, fine_grams_a, fine_grams_b,
        and notional values if prices were provided. Unpackable as (lots_a, lots_b, residual_fine_g).
    """
    # Parse flexible positional arguments
    if len(args) == 4:
        # Called as (tu_a, purity_a, tu_b, purity_b)
        trading_unit_a, purity_a, trading_unit_b, purity_b = args
    elif len(args) == 3:
        # Called as (g_a, g_b, max_lots_per_leg)
        g_a, g_b, max_lots_per_leg = args
    elif len(args) == 2:
        # Called as (g_a, g_b)
        g_a, g_b = args
    elif len(args) == 1:
        g_a = args[0]

    # Resolve g_a
    if g_a is None:
        if trading_unit_a is not None and purity_a is not None:
            g_a = fine_grams_per_lot(trading_unit_a, purity_a, target_purity)
        else:
            raise ValueError("Must provide g_a or (trading_unit_a, purity_a).")

    # Resolve g_b
    if g_b is None:
        if trading_unit_b is not None and purity_b is not None:
            g_b = fine_grams_per_lot(trading_unit_b, purity_b, target_purity)
        else:
            raise ValueError("Must provide g_b or (trading_unit_b, purity_b).")

    if g_a <= 0:
        raise ValueError(f"g_a must be strictly positive, got {g_a}")
    if g_b <= 0:
        raise ValueError(f"g_b must be strictly positive, got {g_b}")
    if max_lots_per_leg < 1:
        raise ValueError(f"max_lots_per_leg must be at least 1, got {max_lots_per_leg}")

    # Determine price per fine gram for notional calculations
    price_per_fine_g_a: Optional[float] = None
    price_per_fine_g_b: Optional[float] = None

    if price_a is not None or price_b is not None:
        eff_p_a = price_a if price_a is not None else price_b
        eff_p_b = price_b if price_b is not None else price_a

        # In AurumLens, normalized prices are in ₹ per 10g of 999 gold.
        # Price per fine gram = normalized_price / 10.0
        price_per_fine_g_a = eff_p_a / 10.0 if eff_p_a is not None else None
        price_per_fine_g_b = eff_p_b / 10.0 if eff_p_b is not None else None

    best_pair: Optional[Tuple[int, int]] = None
    best_abs_diff = float("inf")
    best_notional_metric = float("inf")

    # Search integers 1 <= n_A, n_B <= max_lots_per_leg
    for n_a in range(1, max_lots_per_leg + 1):
        for n_b in range(1, max_lots_per_leg + 1):
            fine_a = n_a * g_a
            fine_b = n_b * g_b
            abs_diff = abs(fine_a - fine_b)

            # Notional check if prices provided
            if price_per_fine_g_a is not None and price_per_fine_g_b is not None:
                notional_a = fine_a * price_per_fine_g_a
                notional_b = fine_b * price_per_fine_g_b
                leg_max_notional = max(notional_a, notional_b)
                if max_notional_inr is not None and leg_max_notional > max_notional_inr:
                    continue
                notional_metric = notional_a + notional_b
            else:
                # If prices not provided, notional is proportional to fine gold weight
                notional_metric = fine_a + fine_b

            # Compare candidate: primary |diff|, secondary notional_metric, tertiary (n_a, n_b)
            if abs_diff < best_abs_diff - 1e-9:
                best_abs_diff = abs_diff
                best_notional_metric = notional_metric
                best_pair = (n_a, n_b)
            elif abs(abs_diff - best_abs_diff) <= 1e-9:
                if notional_metric < best_notional_metric - 1e-9:
                    best_notional_metric = notional_metric
                    best_pair = (n_a, n_b)
                elif abs(notional_metric - best_notional_metric) <= 1e-9:
                    if best_pair is not None and (n_a, n_b) < best_pair:
                        best_pair = (n_a, n_b)

    if best_pair is None:
        raise ValueError(
            f"No valid lot combination found within max_notional_inr={max_notional_inr} "
            f"and max_lots_per_leg={max_lots_per_leg}."
        )

    opt_n_a, opt_n_b = best_pair
    total_fine_a = opt_n_a * g_a
    total_fine_b = opt_n_b * g_b
    raw_res = total_fine_a - total_fine_b
    residual_fine_g = 0.0 if abs(raw_res) < 1e-9 else round(raw_res, 6)

    final_notional_a: Optional[float] = None
    final_notional_b: Optional[float] = None
    final_total_notional: Optional[float] = None

    if price_per_fine_g_a is not None and price_per_fine_g_b is not None:
        final_notional_a = round(total_fine_a * price_per_fine_g_a, 2)
        final_notional_b = round(total_fine_b * price_per_fine_g_b, 2)
        final_total_notional = round(final_notional_a + final_notional_b, 2)

    return SizingResult(
        lots_a=opt_n_a,
        lots_b=opt_n_b,
        residual_fine_g=residual_fine_g,
        fine_grams_a=round(total_fine_a, 6),
        fine_grams_b=round(total_fine_b, 6),
        notional_a=final_notional_a,
        notional_b=final_notional_b,
        total_notional=final_total_notional,
    )


# Convenience aliases
compute_lot_ratio = calculate_lot_ratio
size_pair = calculate_lot_ratio


def lot_ratio(
    spec_a: Any,
    spec_b: Any,
    max_lots_per_leg: int = 50,
    max_notional_inr: Optional[float] = 2_500_000.0,
    target_purity: float = 0.999,
    **kwargs: Any,
) -> SizingResult:
    """Convenience wrapper accepting specs, dictionaries, or fine gram floats.

    Returns SizingResult which can be unpacked as (lots_a, lots_b, residual_fine_g).
    """
    g_a = _extract_fine_grams(spec_a, target_purity)
    g_b = _extract_fine_grams(spec_b, target_purity)

    return calculate_lot_ratio(
        g_a=g_a,
        g_b=g_b,
        max_lots_per_leg=max_lots_per_leg,
        max_notional_inr=max_notional_inr,
        target_purity=target_purity,
        **kwargs,
    )


def size_contracts(
    symbol_a: str,
    symbol_b: str,
    contracts_config: Any,
    max_lots_per_leg: int = 50,
    max_notional_inr: Optional[float] = 2_500_000.0,
    price_a: Optional[float] = None,
    price_b: Optional[float] = None,
    purity_a_override: Optional[float] = None,
    purity_b_override: Optional[float] = None,
    target_purity: float = 0.999,
) -> SizingResult:
    """Convenience function looking up contract specs from configuration."""
    g_a = _contract_fine_grams_from_config(symbol_a, contracts_config, purity_a_override, target_purity)
    g_b = _contract_fine_grams_from_config(symbol_b, contracts_config, purity_b_override, target_purity)

    return calculate_lot_ratio(
        g_a=g_a,
        g_b=g_b,
        max_lots_per_leg=max_lots_per_leg,
        max_notional_inr=max_notional_inr,
        price_a=price_a,
        price_b=price_b,
        target_purity=target_purity,
    )


def _extract_fine_grams(spec_or_g: Any, target_purity: float = 0.999) -> float:
    """Extract fine grams per lot from a number, dict, or ContractSpecConfig."""
    if isinstance(spec_or_g, (int, float)):
        return float(spec_or_g)

    trading_unit_g: Optional[float] = None
    purity: Optional[float] = None

    if hasattr(spec_or_g, "trading_unit_g"):
        tu = spec_or_g.trading_unit_g
        trading_unit_g = float(tu.value if hasattr(tu, "value") else tu)
    elif isinstance(spec_or_g, dict) and "trading_unit_g" in spec_or_g:
        tu = spec_or_g["trading_unit_g"]
        trading_unit_g = float(tu["value"] if isinstance(tu, dict) and "value" in tu else tu)

    if hasattr(spec_or_g, "purity"):
        p = spec_or_g.purity
        raw_p = p.value if hasattr(p, "value") else p
        purity = float(raw_p) if raw_p is not None else None
    elif isinstance(spec_or_g, dict) and "purity" in spec_or_g:
        p = spec_or_g["purity"]
        raw_p = p["value"] if isinstance(p, dict) and "value" in p else p
        purity = float(raw_p) if raw_p is not None else None

    if trading_unit_g is None or purity is None:
        raise ValueError(f"Could not extract trading_unit_g and purity from spec: {spec_or_g}")

    return fine_grams_per_lot(trading_unit_g, purity, target_purity)


def _contract_fine_grams_from_config(
    symbol: str,
    contracts_config: Any,
    purity_override: Optional[float] = None,
    target_purity: float = 0.999,
) -> float:
    """Helper to lookup contract and return fine grams per lot."""
    cfg = contracts_config
    if hasattr(cfg, "contracts"):
        inner = cfg.contracts
        contracts_map = inner.contracts if hasattr(inner, "contracts") else inner
    elif isinstance(cfg, dict):
        contracts_map = cfg.get("contracts", cfg)
    else:
        raise TypeError(f"Unsupported contracts_config type: {type(contracts_config)}")

    sym_upper = symbol.upper()
    spec = contracts_map.get(sym_upper) or contracts_map.get(symbol)
    if spec is None:
        raise KeyError(f"Symbol '{symbol}' not found in contracts config.")

    trading_unit_g: float
    if hasattr(spec, "trading_unit_g"):
        tu = spec.trading_unit_g
        trading_unit_g = float(tu.value if hasattr(tu, "value") else tu)
    elif isinstance(spec, dict) and "trading_unit_g" in spec:
        tu = spec["trading_unit_g"]
        trading_unit_g = float(tu["value"] if isinstance(tu, dict) and "value" in tu else tu)
    else:
        raise ValueError(f"Contract '{symbol}' missing 'trading_unit_g'.")

    purity: Optional[float] = purity_override
    if purity is None:
        if hasattr(spec, "purity"):
            p = spec.purity
            raw_p = p.value if hasattr(p, "value") else p
            purity = float(raw_p) if raw_p is not None else None
            if purity is None and hasattr(p, "candidates") and p.candidates:
                purity = float(p.candidates[-1])
        elif isinstance(spec, dict) and "purity" in spec:
            p = spec["purity"]
            raw_p = p["value"] if isinstance(p, dict) and "value" in p else p
            purity = float(raw_p) if raw_p is not None else None
            if purity is None and isinstance(p, dict) and "candidates" in p and p["candidates"]:
                purity = float(p["candidates"][-1])

    if purity is None:
        raise ValueError(f"Contract '{symbol}' has undefined purity. Provide purity override.")

    return fine_grams_per_lot(trading_unit_g, purity, target_purity)
