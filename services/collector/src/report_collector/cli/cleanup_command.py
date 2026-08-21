import os

from report_collector.config.settings import Settings
from report_collector.repositories.supabase.postgres_processing_repository import (
    clear_expired_processing_data,
)
from report_collector.services.cleanup_service import cleanup_expired_files


def cleanup_command() -> None:
    settings = Settings.from_environment()
    removed = cleanup_expired_files(settings.temp_file_dir, settings.temp_file_ttl_hours)
    database_url = os.environ.get("DATABASE_URL")
    cleared = clear_expired_processing_data(database_url) if database_url else (0, 0)
    print(
        f"removed {len(removed)} expired temporary files; "
        f"cleared {cleared[0]} file paths and {cleared[1]} text retention markers"
    )
