EXCLUDED_PUBLIC_SOURCE_SLUGS = (
    "fsc-policy",
    "mof-press",
)


def is_public_report_source(source_slug: str) -> bool:
    return source_slug not in EXCLUDED_PUBLIC_SOURCE_SLUGS
