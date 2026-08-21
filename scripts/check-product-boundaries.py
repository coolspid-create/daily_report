from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/web/app"
FORBIDDEN_ROUTE_PARTS = {"reports", "report", "signup", "account", "mypage", "search", "chat"}


def main() -> None:
    public_pages = []
    forbidden = []
    for path in APP.rglob("page.tsx"):
        relative = path.relative_to(APP)
        parts = {part.lower() for part in relative.parts}
        if "admin" not in parts:
            public_pages.append(relative.as_posix())
        if parts & FORBIDDEN_ROUTE_PARTS:
            forbidden.append(relative.as_posix())
    if public_pages != ["(public)/page.tsx"]:
        raise SystemExit(f"unexpected public pages: {public_pages}")
    if forbidden:
        raise SystemExit(f"forbidden product routes: {forbidden}")
    print("product boundary passed: one public page and no forbidden routes")


if __name__ == "__main__":
    main()
