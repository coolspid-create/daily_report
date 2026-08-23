from report_collector.cli import auto_review_command


def test_auto_review_command_scopes_source(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_review(*args: object) -> object:
        captured["args"] = args
        return type("Summary", (), {"candidate_count": 1, "approved_count": 1, "exception_count": 0})()

    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    monkeypatch.setattr(auto_review_command, "auto_review_documents", fake_review)

    auto_review_command.auto_review_command("Asia/Seoul", 168, True, "kif-financial-brief")

    assert captured["args"][-1] == "kif-financial-brief"
    assert "approved=1" in capsys.readouterr().out
