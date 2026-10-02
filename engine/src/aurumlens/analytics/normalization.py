"""Price normalization analytics module for AurumLens.

Implements cross-contract price normalization per Design §6.3 (R16):
Every MCX gold contract is normalized to a common baseline of
Rupees per 10 grams of 0.999 fine gold.

Formula:
    P_norm = P_used * (10 / quote_basis_g) * (target_purity / purity)

where:
    - P_used is the selected price (settlement or close).
    - quote_basis_g is the weight in grams for which the quoted price is stated.
    - purity is the contract fineness (e.g. 0.995 for GOLDM, 0.999 for GOLDTEN).
    - target_purity is 0.999 (999 fineness standard).
    - 10 is the target basis in grams.

Key Direction Property (R16):
    Normalizing a sub-999 purity contract (e.g. 995 fineness) results in a HIGHER
    normalized price than its weight-equivalent price, because pure gold (0.999)
    is worth more per gram than lower-fineness gold (0.995).
    Factor: 0.999 / 0.995 = 1.0040201 (> 1.0).
"""

from typing import Any, Optional


def normalize_price(
    price_used: float,
    quote_basis_g: float,
    purity: float,
    target_purity: float = 0.999,
    target_basis_g: float = 10.0,
) -> float:
    """Normalize a quoted contract price to Rupees per target basis (10g of 0.999 fine gold).

    Per Design §6.3 (R16):
        P_norm = P_used * (target_basis_g / quote_basis_g) * (target_purity / purity)

    Parameters
    ----------
    price_used : float
        Quoted contract price in INR (settlement or close price).
    quote_basis_g : float
        Quote basis in grams (e.g., 10.0 for GOLDM/GOLDTEN, 8.0 for GOLDGUINEA, 1.0 for GOLDPETAL).
    purity : float
        Contract gold purity/fineness as a fraction (e.g., 0.995 for GOLDM, 0.999 for GOLDTEN).
    target_purity : float, optional
        Standard reference purity, default 0.999 (999 fine gold).
    target_basis_g : float, optional
        Standard reference weight in grams, default 10.0.

    Returns
    -------
    float
        Normalized price in ₹ per target_basis_g (10g) of target_purity (999) gold.

    Raises
    ------
    ValueError
        If price_used < 0, or if quote_basis_g <= 0, purity <= 0, target_purity <= 0, or target_basis_g <= 0.
    """
    if price_used < 0:
        raise ValueError(f"price_used cannot be negative, got {price_used}")
    if quote_basis_g <= 0:
        raise ValueError(f"quote_basis_g must be strictly positive, got {quote_basis_g}")
    if purity <= 0:
        raise ValueError(f"purity must be strictly positive, got {purity}")
    if target_purity <= 0:
        raise ValueError(f"target_purity must be strictly positive, got {target_purity}")
    if target_basis_g <= 0:
        raise ValueError(f"target_basis_g must be strictly positive, got {target_basis_g}")

    weight_factor = target_basis_g / quote_basis_g
    purity_factor = target_purity / purity
    return price_used * weight_factor * purity_factor


# Convenience alias matching Phase 2 functional specification
normalize = normalize_price


def normalize_contract_price(
    price_used: float,
    symbol: str,
    contracts_config: Any,
    purity: Optional[float] = None,
    purity_override: Optional[float] = None,
) -> float:
    """Normalize a contract price looking up contract specifications from configuration.

    Parameters
    ----------
    price_used : float
        Quoted contract price in INR.
    symbol : str
        Contract symbol (e.g. 'GOLDM', 'GOLDTEN', 'GOLDGUINEA', 'GOLDPETAL').
    contracts_config : Any
        ContractsConfig instance, LoadedConfig instance, or raw dict from contracts.yaml.
    purity : Optional[float], optional
        Optional purity override (e.g. 0.999 for GOLDGUINEA where purity is DISPUTED).
    purity_override : Optional[float], optional
        Alias for purity override.

    Returns
    -------
    float
        Normalized price in ₹ per 10g of 999 fine gold.

    Raises
    ------
    KeyError
        If symbol is not found in contracts_config.
    ValueError
        If contract purity is undefined / None in config and no override is provided.
    """
    effective_purity_override = purity if purity is not None else purity_override
    quote_basis_g, cfg_purity, target_basis_g, target_purity = _extract_contract_spec(
        symbol=symbol,
        contracts_config=contracts_config,
    )

    final_purity = effective_purity_override if effective_purity_override is not None else cfg_purity
    if final_purity is None:
        raise ValueError(
            f"Contract '{symbol}' has undefined or DISPUTED purity in config. "
            "Please provide an explicit 'purity' or 'purity_override' argument (e.g. 0.999)."
        )

    return normalize_price(
        price_used=price_used,
        quote_basis_g=quote_basis_g,
        purity=final_purity,
        target_purity=target_purity,
        target_basis_g=target_basis_g,
    )


def purity_direction_test(
    price: float,
    purity: float,
    quote_basis_g: float = 10.0,
    target_purity: float = 0.999,
    target_basis_g: float = 10.0,
) -> bool:
    """Validate that normalizing a sub-999 purity contract results in a HIGHER price.

    Per Design §6.3 (R16):
        Normalizing a sub-999 contract (e.g. 995 fineness) must produce a value
        greater than its weight-equivalent price, because 999 gold is purer
        than 995 gold: factor = 0.999 / purity > 1.0.

    Parameters
    ----------
    price : float
        Quoted price of the contract.
    purity : float
        Fineness of the contract (e.g. 0.995).
    quote_basis_g : float, optional
        Quote basis in grams (default: 10.0).
    target_purity : float, optional
        Standard reference purity (default: 0.999).
    target_basis_g : float, optional
        Standard reference weight in grams (default: 10.0).

    Returns
    -------
    bool
        True if the normalized price is strictly greater than the price scaled
        only by weight for purity < target_purity; False otherwise.
    """
    if purity >= target_purity:
        return False
    norm_price = normalize_price(
        price_used=price,
        quote_basis_g=quote_basis_g,
        purity=purity,
        target_purity=target_purity,
        target_basis_g=target_basis_g,
    )
    weight_equivalent = price * (target_basis_g / quote_basis_g)
    return norm_price > weight_equivalent


def _extract_contract_spec(
    symbol: str,
    contracts_config: Any,
) -> tuple[float, Optional[float], float, float]:
    """Helper to extract quote_basis_g, purity, target_basis_g, target_purity."""
    cfg = contracts_config
    if hasattr(cfg, "contracts"):
        inner = cfg.contracts
        if hasattr(inner, "contracts"):
            contracts_map = inner.contracts
            target_basis_obj = getattr(inner, "target_basis", None)
        else:
            contracts_map = inner
            target_basis_obj = getattr(cfg, "target_basis", None)
    elif isinstance(cfg, dict):
        if "contracts" in cfg:
            contracts_map = cfg["contracts"]
            target_basis_obj = cfg.get("target_basis")
        else:
            contracts_map = cfg
            target_basis_obj = None
    else:
        raise TypeError(f"Unsupported contracts_config type: {type(contracts_config)}")

    target_basis_g = 10.0
    target_purity = 0.999
    if target_basis_obj is not None:
        if isinstance(target_basis_obj, dict):
            target_basis_g = float(target_basis_obj.get("grams", 10.0))
            target_purity = float(target_basis_obj.get("purity", 0.999))
        else:
            target_basis_g = float(getattr(target_basis_obj, "grams", 10.0))
            target_purity = float(getattr(target_basis_obj, "purity", 0.999))

    sym_upper = symbol.upper()
    spec = None
    if isinstance(contracts_map, dict):
        spec = contracts_map.get(sym_upper) or contracts_map.get(symbol)
    else:
        spec = getattr(contracts_map, sym_upper, None) or getattr(contracts_map, symbol, None)

    if spec is None:
        raise KeyError(f"Contract symbol '{symbol}' not found in contracts configuration.")

    if hasattr(spec, "quote_basis_g"):
        val = spec.quote_basis_g
        quote_basis_g = float(val.value if hasattr(val, "value") else val)
    elif isinstance(spec, dict) and "quote_basis_g" in spec:
        val = spec["quote_basis_g"]
        quote_basis_g = float(val["value"] if isinstance(val, dict) and "value" in val else val)
    else:
        raise ValueError(f"Contract spec for '{symbol}' missing 'quote_basis_g'.")

    purity: Optional[float] = None
    if hasattr(spec, "purity"):
        val = spec.purity
        raw_val = val.value if hasattr(val, "value") else val
        purity = float(raw_val) if raw_val is not None else None
    elif isinstance(spec, dict) and "purity" in spec:
        val = spec["purity"]
        raw_val = val["value"] if isinstance(val, dict) and "value" in val else val
        purity = float(raw_val) if raw_val is not None else None

    return quote_basis_g, purity, target_basis_g, target_purity
