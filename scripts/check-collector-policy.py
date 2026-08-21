from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ADAPTERS = {"static_board", "rendered_board", "rss"}
FORBIDDEN_URL_MARKERS = ("/api/", "/openapi/", ".json", "ajax", "xhr")
FORBIDDEN_CLIENT_IMPORTS = ("import httpx", "import requests", "import aiohttp")


def main() -> None:
    failures: list[str] = []
    for path in sorted((ROOT / "config/sources").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if data.get("adapter") not in ALLOWED_ADAPTERS:
            failures.append(f"{path.name}: unsupported adapter")
        for field in ("homepage_url", "list_url"):
            url = str(data.get(field, ""))
            parsed = urlparse(url)
            lowered = parsed.path.lower()
            if any(marker in lowered for marker in FORBIDDEN_URL_MARKERS):
                failures.append(f"{path.name}: forbidden endpoint in {field}")
    adapters = ROOT / "services/collector/src/report_collector/adapters"
    for path in adapters.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        if any(marker in text for marker in FORBIDDEN_CLIENT_IMPORTS):
            failures.append(f"{path.relative_to(ROOT)}: direct network client")
    if failures:
        raise SystemExit("\n".join(failures))
    print("collector policy passed: HTML/RSS/browser only, no direct API client")


if __name__ == "__main__":
    main()
