from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {"node_modules", ".next", ".venv", "coverage", "generated"}
LIMITS = {".ts": 350, ".tsx": 220, ".py": 350}
TEST_LIMIT = 450


def limit_for(path: Path) -> int | None:
    if path.suffix not in LIMITS:
        return None
    if "tests" in path.parts or path.name.startswith("test_"):
        return TEST_LIMIT
    return LIMITS[path.suffix]


def violations() -> list[str]:
    results: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        limit = limit_for(path)
        if limit is None:
            continue
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > limit:
            results.append(f"{path.relative_to(ROOT)}: {count} lines (limit {limit})")
    return results


def main() -> int:
    problems = violations()
    if problems:
        print("File-size violations:")
        print("\n".join(problems))
        return 1
    print("File-size rules passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
