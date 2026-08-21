from hashlib import sha256
from pathlib import Path


class LocalDigestStorage:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def target(self, date_label: str, topic_id: str) -> Path:
        safe_topic = "".join(
            character for character in topic_id if character.isalnum() or character in {"-", "_"}
        )
        return self.output_dir / f"{date_label}-{safe_topic}.pdf"

    def metadata(self, path: Path) -> dict[str, str | int]:
        content = path.read_bytes()
        return {
            "path": str(path),
            "size_bytes": len(content),
            "checksum": sha256(content).hexdigest(),
        }
