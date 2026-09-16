"""Read-only list-page probes; no database credentials, publication or Telegram."""
import asyncio
import json
import time
from pathlib import Path

from report_collector.config.source_config import load_source_config
from report_collector.providers.http.http_client import PublicHttpClient

ROOT = Path(__file__).resolve().parents[1]


async def probe(slug: str) -> None:
    config = load_source_config(
        ROOT / f"config/sources/{slug}.yaml", ROOT / "contracts/source-config.schema.json"
    )
    started = time.monotonic()
    try:
        result = await PublicHttpClient(timeout=15, retries=0, delay_ms=0).fetch(
            str(config.list_url)
        )
        outcome = {"result": "HTTP_OK", "bytes": len(result.content), "url": result.final_url}
    except Exception as error:
        outcome = {"result": type(error).__name__}
    print(json.dumps({"source": slug, "seconds": round(time.monotonic() - started, 2), **outcome}))


async def main() -> None:
    for slug in ("molit-press", "ftc-press", "motie-press", "msit-press", "ibks-research"):
        await probe(slug)


if __name__ == "__main__":
    asyncio.run(main())
