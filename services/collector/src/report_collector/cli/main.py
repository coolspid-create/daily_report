import os
from argparse import ArgumentParser
from pathlib import Path

from ..config.settings import load_repository_environment
from .cleanup_command import cleanup_command
from .collect_command import collect_command
from .daily_publish_command import daily_publish_command
from .digest_command import digest_command
from .snapshot_command import snapshot_command


def parser() -> ArgumentParser:
    root = Path.cwd()
    result = ArgumentParser(prog="report_collector")
    commands = result.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("collect")
    group = collect.add_mutually_exclusive_group(required=True)
    group.add_argument("--source")
    group.add_argument("--all-active", action="store_true")
    collect.add_argument("--refresh-recent", action="store_true")
    collect.add_argument("--config-root", type=Path, default=root / "config/sources")
    snapshot = commands.add_parser("build-snapshot")
    snapshot.add_argument("--date", required=True)
    snapshot.add_argument("--range", choices=["today", "1d", "7d"], default="7d")
    snapshot.add_argument("--output-dir", type=Path, default=root / "output/pdf")
    digest = commands.add_parser("build-digest")
    digest.add_argument("--date", required=True)
    digest.add_argument("--topic", required=True)
    digest.add_argument("--range", choices=["today", "1d", "7d"], default="7d")
    digest.add_argument("--output-dir", type=Path, default=root / "output/pdf")
    digest.add_argument("--snapshot-file", type=Path)
    cleanup = commands.add_parser("cleanup")
    cleanup.add_argument("--expired-files", action="store_true", required=True)
    daily = commands.add_parser("daily-publish")
    daily.add_argument("--timezone", default=os.getenv("AUTOMATION_TIMEZONE", "Asia/Seoul"))
    daily.add_argument("--window-hours", type=int, default=int(os.getenv("AUTOMATION_WINDOW_HOURS", "168")))
    daily.add_argument("--output-dir", type=Path, default=root / "output/pdf")
    daily.add_argument("--dry-run", action="store_true")
    daily.add_argument("--scheduled-run", action="store_true")
    return result


def main() -> None:
    root = Path.cwd()
    load_repository_environment(root)
    arguments = parser().parse_args()
    if arguments.command == "collect":
        collect_command(
            arguments.source,
            arguments.all_active,
            arguments.config_root,
            root / "contracts/source-config.schema.json",
            arguments.refresh_recent,
        )
    elif arguments.command == "build-snapshot":
        snapshot_command(
            arguments.date,
            arguments.range,
            root / "contracts/public-feed.schema.json",
            arguments.output_dir,
        )
    elif arguments.command == "build-digest":
        digest_command(
            arguments.date,
            arguments.topic,
            arguments.range,
            arguments.output_dir,
            arguments.snapshot_file,
        )
    elif arguments.command == "cleanup":
        cleanup_command()
    elif arguments.command == "daily-publish":
        daily_publish_command(
            root,
            arguments.timezone,
            arguments.window_hours,
            arguments.output_dir,
            arguments.dry_run,
            arguments.scheduled_run,
        )
