from datetime import UTC, datetime, timedelta
from pathlib import Path


def cleanup_expired_files(
    directory: Path, ttl_hours: int, now: datetime | None = None
) -> list[Path]:
    cutoff = (now or datetime.now(UTC)) - timedelta(hours=ttl_hours)
    removed: list[Path] = []
    if not directory.exists():
        return removed
    for path in directory.iterdir():
        if not path.is_file():
            continue
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        if modified < cutoff:
            path.unlink()
            removed.append(path)
    return removed
