import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    path = ROOT / ".github/workflows/collector.yml"
    text = path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    triggers = workflow.get(True, {})
    vercel_config = json.loads((ROOT / "apps/web/vercel.json").read_text(encoding="utf-8"))
    crons = vercel_config.get("crons", [])
    required = [
        "daily-publish --timezone Asia/Seoul --window-hours 168",
        "scheduled_run",
        "concurrency:",
    ]
    missing = [item for item in required if item not in text]
    expected_crons = [{"path": "/api/cron/daily-publish", "schedule": "35 23 * * *"}]
    if missing or "workflow_dispatch" not in triggers or crons != expected_crons:
        raise SystemExit(f"automation workflow contract failed: {missing or crons}")
    print("automation workflow passed: Vercel Cron dispatches one seven-day orchestrator command at 08:35 KST")


if __name__ == "__main__":
    main()
