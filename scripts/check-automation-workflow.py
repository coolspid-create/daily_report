import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    path = ROOT / ".github/workflows/collector.yml"
    text = path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    triggers = workflow.get(True, {})
    watchdog_path = ROOT / ".github/workflows/press-collection-watchdog.yml"
    watchdog_text = watchdog_path.read_text(encoding="utf-8")
    watchdog = yaml.safe_load(watchdog_text)
    watchdog_triggers = watchdog.get(True, {})
    vercel_config = json.loads((ROOT / "apps/web/vercel.json").read_text(encoding="utf-8"))
    crons = vercel_config.get("crons", [])
    required = [
        "daily-publish --timezone Asia/Seoul --window-hours 168",
        "scheduled_run",
        "run_mode",
        "publish-approved",
        "concurrency:",
        "FEED_REVALIDATION_SECRET",
    ]
    missing = [item for item in required if item not in text]
    expected_crons = [
        {"path": "/api/cron/daily-publish", "schedule": "35 23 * * 0-4"},
        {"path": "/api/cron/press-collect", "schedule": "30 1 * * 0-4"},
    ]
    watchdog_schedule = {"cron": "45 2 * * 0-4"}
    watchdog_required = [
        "createWorkflowDispatch",
        'run_mode: "press"',
        "TELEGRAM_BOT_TOKEN",
        "fallback_required",
    ]
    missing_watchdog = [item for item in watchdog_required if item not in watchdog_text]
    if (
        missing
        or missing_watchdog
        or "workflow_dispatch" not in triggers
        or "workflow_dispatch" not in watchdog_triggers
        or watchdog_schedule not in watchdog_triggers.get("schedule", [])
        or crons != expected_crons
    ):
        raise SystemExit(
            f"automation workflow contract failed: {missing or missing_watchdog or crons}"
        )
    print(
        "automation workflow passed: Vercel Cron dispatches report collection at 08:35 "
        "and press collection at 10:30 on KST weekdays with an 11:45 Actions fallback"
    )


if __name__ == "__main__":
    main()
