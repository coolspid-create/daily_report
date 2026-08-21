from report_collector.domain.models import FilterConfig


def title_allowed(title: str, filters: FilterConfig) -> bool:
    if any(keyword in title for keyword in filters.exclude_title_keywords):
        return False
    if filters.include_title_keywords:
        return any(keyword in title for keyword in filters.include_title_keywords)
    return True
