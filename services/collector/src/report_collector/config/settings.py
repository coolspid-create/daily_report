import os
from pathlib import Path

from pydantic import BaseModel, Field


def load_repository_environment(root: Path) -> None:
    environment_file = root / ".env"
    if not environment_file.exists():
        return
    for raw_line in environment_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", maxsplit=1)
        if key and key not in os.environ:
            os.environ[key] = value


class Settings(BaseModel):
    temp_file_dir: Path = Path(".data/temporary-source-files")
    max_download_bytes: int = Field(default=52_428_800, gt=0)
    default_request_delay_ms: int = Field(default=1200, ge=500)
    playwright_enabled: bool = True
    temp_file_ttl_hours: int = Field(default=48, ge=24, le=72)
    pdf_processing_attempts: int = Field(default=3, ge=1, le=5)
    pdf_ocr_enabled: bool = False

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            temp_file_dir=Path(os.getenv("TEMP_FILE_DIR", ".data/temporary-source-files")),
            max_download_bytes=int(os.getenv("MAX_DOWNLOAD_BYTES", "52428800")),
            default_request_delay_ms=int(os.getenv("DEFAULT_REQUEST_DELAY_MS", "1200")),
            playwright_enabled=os.getenv("PLAYWRIGHT_ENABLED", "true").lower() == "true",
            temp_file_ttl_hours=int(os.getenv("TEMP_FILE_TTL_HOURS", "48")),
            pdf_processing_attempts=int(os.getenv("PDF_PROCESSING_ATTEMPTS", "3")),
            pdf_ocr_enabled=os.getenv("PDF_OCR_ENABLED", "false").lower() == "true",
        )
