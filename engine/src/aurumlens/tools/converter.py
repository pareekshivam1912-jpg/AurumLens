"""Contract Price Converter Tool (FR22).

Given any contract's quoted price, computes its normalized equivalent in
Rupees per 10 grams of 0.999 fine gold, and the mathematically equivalent
quoted price for every other contract in the universe.

Quant Invariant:
    P_norm = P_quoted * (10 / quote_basis_g) * (0.999 / purity)
    P_equiv = P_norm * (quote_basis_g_target / 10) * (purity_target / 0.999)

Analytics only — not investment advice.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from aurumlens.analytics.normalization import normalize_contract_price, normalize_price
from aurumlens.config.models import ContractsConfig

DISCLAIMER: str = "Analytics only — not investment advice"


@dataclass(frozen=True)
class ContractEquivalent:
    """Equivalent price representation for a specific contract."""
    symbol: str
    equivalent_quoted_price: float
    quote_basis_g: float
    purity: float
    purity_status: str


@dataclass(frozen=True)
class ConversionResult:
    """Complete conversion result across all contracts in the universe."""
    source_symbol: str
    source_quoted_price: float
    normalized_price_10g_999: float
    equivalents: Dict[str, ContractEquivalent]
    disclaimer: str = DISCLAIMER


def denormalize_price(
    normalized_price: float,
    quote_basis_g: float,
    purity: float,
    target_purity: float = 0.999,
    target_basis_g: float = 10.0,
) -> float:
    """Convert a normalized price (Rs per target_basis_g of target_purity) back to a contract's quoted price."""
    if normalized_price < 0:
        raise ValueError(f"normalized_price cannot be negative, got {normalized_price}")
    if quote_basis_g <= 0 or purity <= 0 or target_purity <= 0 or target_basis_g <= 0:
        raise ValueError("Basis weights and purities must be strictly positive")

    weight_factor = quote_basis_g / target_basis_g
    purity_factor = purity / target_purity
    return normalized_price * weight_factor * purity_factor


def convert_contract_price(
    source_symbol: str,
    quoted_price: float,
    contracts_config: ContractsConfig,
    purity_override: Optional[float] = None,
) -> ConversionResult:
    """Convert a quoted contract price to normalized basis and all other contract quote bases.

    Parameters
    ----------
    source_symbol : str
        Source contract symbol (e.g. 'GOLDTEN', 'GOLDM', 'GOLDGUINEA', 'GOLDPETAL').
    quoted_price : float
        Quoted price in INR for the source contract.
    contracts_config : ContractsConfig
        Configuration containing contract specifications and purities.
    purity_override : Optional[float]
        Optional purity override (e.g. For DISPUTED contracts in research mode).

    Returns
    -------
    ConversionResult
        Structured conversion result with normalized price and all contract equivalents.
    """
    if source_symbol not in contracts_config.contracts:
        raise KeyError(
            f"Symbol '{source_symbol}' not found in contracts config. "
            f"Available: {list(contracts_config.contracts.keys())}"
        )

    # 1. Normalize source price
    norm_price = normalize_contract_price(
        price_used=quoted_price,
        symbol=source_symbol,
        contracts_config=contracts_config,
        purity_override=purity_override,
    )

    # 2. Compute equivalents for all contracts
    equivalents: Dict[str, ContractEquivalent] = {}
    for sym, spec in contracts_config.contracts.items():
        qb = float(spec.quote_basis_g.value or 10.0)
        p = float(spec.purity.value or 0.999)
        p_status = spec.purity.status.value

        equiv_price = denormalize_price(
            normalized_price=norm_price,
            quote_basis_g=qb,
            purity=p,
            target_purity=contracts_config.target_basis.purity,
            target_basis_g=contracts_config.target_basis.grams,
        )

        equivalents[sym] = ContractEquivalent(
            symbol=sym,
            equivalent_quoted_price=round(equiv_price, 2),
            quote_basis_g=qb,
            purity=p,
            purity_status=p_status,
        )

    return ConversionResult(
        source_symbol=source_symbol,
        source_quoted_price=round(quoted_price, 2),
        normalized_price_10g_999=round(norm_price, 2),
        equivalents=equivalents,
        disclaimer=DISCLAIMER,
    )
