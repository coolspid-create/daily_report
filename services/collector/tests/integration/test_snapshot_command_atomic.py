from pathlib import Path

import pytest
from report_collector.cli import snapshot_command as command_module


def test_digest_failure_does_not_activate_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    statuses: list[str] = []
    activated = False

    async def fail_render(*_args, **_kwargs):
        raise RuntimeError("digest failed")

    def unexpected_publish(*_args, **_kwargs):
        nonlocal activated
        activated = True

    monkeypatch.setenv("DATABASE_URL", "postgresql://fixture")
    monkeypatch.setenv("SUPABASE_URL", "https://fixture.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fixture-key")
    monkeypatch.setattr(command_module, "load_approved_documents", lambda *_: [])
    monkeypatch.setattr(command_module, "ensure_publication", lambda *_: "publication-id")
    monkeypatch.setattr(command_module, "_render_digests", fail_render)
    monkeypatch.setattr(command_module, "publish_snapshot", unexpected_publish)
    monkeypatch.setattr(
        command_module,
        "set_publication_status",
        lambda _url, _id, status: statuses.append(status),
    )

    with pytest.raises(RuntimeError, match="digest failed"):
        command_module.snapshot_command("2026-08-21", "today", tmp_path / "schema.json", tmp_path)

    assert activated is False
    assert statuses == ["FAILED"]
