from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    path = ROOT / ".github/workflows/collector.yml"
    text = path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    schedules = workflow.get(True, {}).get("schedule", [])
    crons = {item.get("cron") for item in schedules}
    required = [
        "daily-publish --timezone Asia/Seoul --window-hours 168",
        "concurrency:",
        'cron: "35 23 * * *"',
    ]
    missing = [item for item in required if item not in text]
    if missing or crons != {"35 23 * * *"}:
        raise SystemExit(f"automation workflow contract failed: {missing or crons}")
    print("automation workflow passed: 08:35 KST and one seven-day orchestrator command")


if __name__ == "__main__":
    main()
