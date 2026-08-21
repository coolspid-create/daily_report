from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "0001_core_sources.sql": ["source_runs", "source_items"],
    "0002_documents_and_files.sql": ["documents", "document_files", "LINK_ONLY"],
    "0003_analysis_and_topics.sql": ["document_analysis", "document_topics"],
    "0004_review_and_publication.sql": ["feed_snapshots", "digest_files"],
    "0005_rls_and_policies.sql": ["enable row level security", "activate_snapshot"],
    "0006_admin_merge.sql": ["merge_documents", "source_document", "review_actions"],
    "0007_digest_storage.sql": ["storage.buckets", "digests_public_read"],
    "0008_analysis_key_tags.sql": ["key_tags", "jsonb_array_length"],
    "0022_automation_delivery.sql": [
        "automation_runs",
        "telegram_deliveries",
        "auto_approve",
        "enable row level security",
    ],
    "0023_public_archive_and_seven_day_publication.sql": [
        "publication_items",
        "public_archive_dates",
        "public_archive_snapshot",
        "7d",
    ],
}


def main() -> None:
    migrations = ROOT / "supabase/migrations"
    for name, terms in REQUIRED.items():
        text = (migrations / name).read_text(encoding="utf-8").lower()
        missing = [term for term in terms if term.lower() not in text]
        if missing:
            raise SystemExit(f"{name}: missing {missing}")
        print(f"migration contract passed: {name}")


if __name__ == "__main__":
    main()
