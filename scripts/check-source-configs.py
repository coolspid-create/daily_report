import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    schema = json.loads((ROOT / "contracts/source-config.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    paths = sorted((ROOT / "config/sources").glob("*.yaml"))
    for path in paths:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        validator.validate(payload)
        print(f"valid source: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
