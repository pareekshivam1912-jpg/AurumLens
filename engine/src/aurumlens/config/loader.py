"""Configuration loader and version hash calculator for AurumLens."""

import hashlib
from pathlib import Path
from typing import NamedTuple, Tuple
import yaml

from aurumlens.config.models import (
    ContractsConfig,
    CostsConfig,
    EventsConfig,
    StrategyConfig,
)


class LoadedConfig(NamedTuple):
    contracts: ContractsConfig
    costs: CostsConfig
    strategy: StrategyConfig
    events: EventsConfig
    config_version: str


def compute_config_version(config_dir: Path) -> str:
    """Compute deterministic config_version = sha256(all config files)[:12].
    
    Files are hashed in sorted order by filename to ensure determinism across platforms.
    """
    files_to_hash = ["contracts.yaml", "costs.yaml", "events.yaml", "strategy.yaml"]
    hasher = hashlib.sha256()

    for fname in sorted(files_to_hash):
        fpath = config_dir / fname
        if fpath.exists():
            with open(fpath, "rb") as f:
                hasher.update(fname.encode("utf-8"))
                hasher.update(f.read())
        else:
            raise FileNotFoundError(f"Required configuration file missing: {fpath}")

    return hasher.hexdigest()[:12]


def load_yaml_dict(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_contracts_config(path: Path) -> ContractsConfig:
    """Load and validate contracts.yaml."""
    raw = load_yaml_dict(path)
    return ContractsConfig.model_validate(raw)


def load_costs_config(path: Path) -> CostsConfig:
    """Load and validate costs.yaml."""
    raw = load_yaml_dict(path)
    return CostsConfig.model_validate(raw)


def load_strategy_config(path: Path) -> StrategyConfig:
    """Load and validate strategy.yaml."""
    raw = load_yaml_dict(path)
    return StrategyConfig.model_validate(raw)


def load_events_config(path: Path) -> EventsConfig:
    """Load and validate events.yaml."""
    raw = load_yaml_dict(path)
    return EventsConfig.model_validate(raw)


def load_all_configs(config_dir: Path) -> LoadedConfig:
    """Load and validate all YAML configurations and stamp with config_version."""
    contracts = load_contracts_config(config_dir / "contracts.yaml")
    costs = load_costs_config(config_dir / "costs.yaml")
    strategy = load_strategy_config(config_dir / "strategy.yaml")
    events = load_events_config(config_dir / "events.yaml")

    config_version = compute_config_version(config_dir)

    return LoadedConfig(
        contracts=contracts,
        costs=costs,
        strategy=strategy,
        events=events,
        config_version=config_version,
    )
