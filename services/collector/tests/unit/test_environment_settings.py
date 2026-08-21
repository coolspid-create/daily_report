import os
from pathlib import Path

from report_collector.config.settings import load_repository_environment


def test_load_repository_environment_preserves_existing_values(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / ".env").write_text(
        "DATABASE_URL=postgresql://fixture\n# ignored\nEMPTY=\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://existing")
    monkeypatch.delenv("EMPTY", raising=False)

    load_repository_environment(tmp_path)

    assert os.environ["DATABASE_URL"] == "postgresql://existing"
    assert os.environ["EMPTY"] == ""
