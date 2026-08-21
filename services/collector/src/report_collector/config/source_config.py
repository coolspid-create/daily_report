import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from report_collector.domain.models import SourceConfig


def load_source_config(path: Path, schema_path: Path | None = None) -> SourceConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if schema_path:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
    return SourceConfig.model_validate(payload)
