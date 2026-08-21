from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .digest_view_model import DigestViewModel


def build_digest_html(view_model: DigestViewModel, template_dir: Path) -> str:
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = environment.get_template("digest.html.j2")
    css = (template_dir / "digest.css").read_text(encoding="utf-8")
    return template.render(view=view_model, css=css)
