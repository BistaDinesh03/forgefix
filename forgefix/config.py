"""Configuration handling for ForgeFix (.forgefix.yml)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

CONFIG_NAME = ".forgefix.yml"


class ForgeFixConfig(BaseModel):
    """User-tunable settings stored in ``.forgefix.yml``."""

    report_path: str = "reports/forgefix-report.md"
    disabled_rules: list[str] = Field(default_factory=list)
    min_score: int = 80


def config_file(root: Path) -> Path:
    """Return the path of the config file inside ``root``."""
    return root / CONFIG_NAME


def load_config(root: Path) -> ForgeFixConfig:
    """Load config from ``root``; missing or invalid files fall back to defaults."""
    path = config_file(root)
    if not path.is_file():
        return ForgeFixConfig()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return ForgeFixConfig()
    if not isinstance(raw, dict):
        return ForgeFixConfig()
    try:
        return ForgeFixConfig.model_validate(raw)
    except ValueError:
        return ForgeFixConfig()


def save_config(root: Path, config: ForgeFixConfig) -> Path:
    """Write ``config`` to ``root`` and return the file path (never overwrites)."""
    path = config_file(root)
    if path.exists():
        return path
    root.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(config.model_dump(), sort_keys=False, default_flow_style=False)
    header = "# ForgeFix configuration - https://github.com/BistaDinesh03/forgefix\n"
    path.write_text(header + payload, encoding="utf-8", newline="\n")
    return path
