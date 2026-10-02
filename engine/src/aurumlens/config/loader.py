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


def load_all_configs(config_dir: Path) -> LoadedConfig:
    """Load and validate all YAML configurations and stamp with config_version."""
    contracts_raw = load_yaml_dict(config_dir / "contracts.yaml")
    costs_raw = load_yaml_dict(config_dir / "costs.yaml")
    strategy_raw = load_yaml_dict(config_dir / "strategy.yaml")
    events_raw = load_yaml_dict(config_dir / "events.yaml")

    contracts = ContractsConfig.model_validate(contracts_raw)
    costs = CostsConfig.model_validate(costs_raw)
    strategy = StrategyConfig.model_validate(strategy_raw)
    events = EventsConfig.model_validate(events_raw)

    config_version = compute_config_version(config_dir)

    return LoadedConfig(
        contracts=contracts,
        costs=costs,
        strategy=strategy,
        events=events,
        config_version=config_version,
    )
