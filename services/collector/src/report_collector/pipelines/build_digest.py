from pathlib import Path
from typing import Any

from report_collector.digest.digest_builder import build_digest_html
from report_collector.digest.digest_renderer import render_digest_pdf
from report_collector.digest.digest_storage import LocalDigestStorage
from report_collector.digest.digest_view_model import build_digest_view_model

TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "digest/templates"


async def build_digest(
    snapshot: dict[str, Any], topic_id: str, output_dir: Path
) -> dict[str, str | int]:
    view_model = build_digest_view_model(snapshot, topic_id)
    html = build_digest_html(view_model, TEMPLATE_ROOT)
    storage = LocalDigestStorage(output_dir)
    path = storage.target(view_model.date_label, topic_id)
    await render_digest_pdf(html, path)
    return storage.metadata(path)
