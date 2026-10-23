"""Config loading/saving tests."""

from pathlib import Path

from forgefix.config import (
    CONFIG_NAME,
    ForgeFixConfig,
    config_file,
    load_config,
    save_config,
)


def test_defaults_when_file_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    assert config == ForgeFixConfig()
    assert config.report_path == "reports/forgefix-report.md"
    assert config.min_score == 80
    assert config.disabled_rules == []
    assert config.ignore == []


def test_ignore_key_loads(tmp_path: Path) -> None:
    (tmp_path / CONFIG_NAME).write_text("ignore: [lockfile, pinned_deps]\n", encoding="utf-8")
    assert load_config(tmp_path).ignore == ["lockfile", "pinned_deps"]


def test_invalid_yaml_falls_back(tmp_path: Path) -> None:
    (tmp_path / CONFIG_NAME).write_text("{{{ not: [yaml\n", encoding="utf-8")
    assert load_config(tmp_path) == ForgeFixConfig()


def test_non_mapping_yaml_falls_back(tmp_path: Path) -> None:
    (tmp_path / CONFIG_NAME).write_text("- one\n- two\n", encoding="utf-8")
    assert load_config(tmp_path) == ForgeFixConfig()


def test_wrong_types_fall_back(tmp_path: Path) -> None:
    (tmp_path / CONFIG_NAME).write_text("min_score: 'not-a-number'\n", encoding="utf-8")
    assert load_config(tmp_path) == ForgeFixConfig()


def test_save_load_roundtrip(tmp_path: Path) -> None:
    config = ForgeFixConfig(
        report_path="custom/report.md",
        disabled_rules=["demo"],
        ignore=["lockfile", "pinned_deps"],
        min_score=55,
    )
    save_config(tmp_path, config)
    loaded = load_config(tmp_path)
    assert loaded == config
    assert "https://github.com/BistaDinesh03/forgefix" in (tmp_path / CONFIG_NAME).read_text(
        encoding="utf-8"
    )


def test_save_never_overwrites(tmp_path: Path) -> None:
    save_config(tmp_path, ForgeFixConfig(report_path="first.md"))
    save_config(tmp_path, ForgeFixConfig(report_path="second.md"))
    assert load_config(tmp_path).report_path == "first.md"


def test_config_file_path(tmp_path: Path) -> None:
    assert config_file(tmp_path) == tmp_path / CONFIG_NAME
