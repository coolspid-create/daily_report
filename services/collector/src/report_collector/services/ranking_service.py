from datetime import date

from report_collector.domain.models import PublicationDocument


def calculate_score(document: PublicationDocument, publication_date: date) -> float:
    freshness_days = max((publication_date - document.published_at).days, 0)
    freshness = max(0.0, 1 - freshness_days / 30)
    relevance = max(0.0, min(document.ranking_score, 1.0))
    has_quantitative_point = any(
        any(character.isdigit() for character in point) for point in document.key_points
    )
    quantitative = 1.0 if has_quantitative_point else 0.4
    return round(relevance * 35 + freshness * 20 + 15 + 15 + quantitative * 10 + 5, 3)


def rank_documents(
    documents: list[PublicationDocument], publication_date: date
) -> list[PublicationDocument]:
    return sorted(
        documents,
        key=lambda item: (calculate_score(item, publication_date), item.published_at),
        reverse=True,
    )


def select_featured_documents(
    documents: list[PublicationDocument], publication_date: date, limit: int = 8
) -> list[PublicationDocument]:
    ranked = rank_documents(documents, publication_date)
    selected: list[PublicationDocument] = []
    institution_counts: dict[str, int] = {}
    for document in ranked:
        count = institution_counts.get(document.institution, 0)
        if count >= 2:
            continue
        selected.append(document)
        institution_counts[document.institution] = count + 1
        if len(selected) == limit:
            break
    return selected
