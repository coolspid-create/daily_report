from pathlib import Path

import pytest
from jsonschema import ValidationError
from report_collector.cli.collect_command import _filter_database_active_paths, _source_paths
from report_collector.config.source_config import load_source_config


def test_all_source_yaml_matches_schema(contract_root: Path, fixture_root: Path) -> None:
    paths = list(Path("config/sources").glob("*.yaml")) + list(
        (fixture_root / "config").glob("*.yaml")
    )
    configs = [
        load_source_config(path, contract_root / "source-config.schema.json") for path in paths
    ]
    assert {config.id for config in configs} >= {
        "nars",
        "kdi-research",
        "bok-rss",
        "krihs-research",
        "sample-static",
        "sample-rendered",
    }


def test_source_schema_rejects_api_adapter(tmp_path: Path, contract_root: Path) -> None:
    path = tmp_path / "api.yaml"
    path.write_text(
        "id: bad\nname: bad\nadapter: api\nhomepage_url: https://example.com\nlist_url: https://example.com/api\nrights_default: LINK_ONLY\npoll_interval_minutes: 60\nrequest_delay_ms: 500\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_source_config(path, contract_root / "source-config.schema.json")


def test_all_active_uses_enabled_source_configs(contract_root: Path) -> None:
    paths = _source_paths(
        None,
        True,
        Path("config/sources"),
        contract_root / "source-config.schema.json",
    )
    names = {path.stem for path in paths}
    assert {
        "bok-rss",
        "nars",
        "krihs-research",
        "kiep-research",
        "kei-research",
        "kiet-research",
        "kedi-research",
        "keei-research",
        "kinu-research",
        "kipf-research",
        "posri-research",
        "hri-research",
        "wfri-research",
        "fki-report",
        "keri-research",
        "ifans-focus",
    } <= names
    assert "kdi-research" not in names
    assert "kihasa-research" not in names
    assert "stepi-research" not in names
    assert "kli-research" not in names


def test_database_deactivation_excludes_an_enabled_source(contract_root: Path) -> None:
    paths = _source_paths(
        None,
        True,
        Path("config/sources"),
        contract_root / "source-config.schema.json",
    )

    filtered = _filter_database_active_paths(paths, {"nars"})

    assert [path.stem for path in filtered] == ["nars"]
