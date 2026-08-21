from report_collector.providers.notifications.base import NotificationProvider
from report_collector.repositories.supabase.postgres_telegram_delivery import (
    begin_telegram_delivery,
    complete_telegram_delivery,
    fail_telegram_delivery,
)
from report_collector.services.telegram_briefing import build_telegram_briefing


def deliver_publication(
    database_url: str,
    publication_id: str,
    publication_date: str,
    snapshot: dict[str, object],
    destination_key: str,
    provider: NotificationProvider,
    web_url: str | None,
) -> int:
    delivery_id = begin_telegram_delivery(database_url, publication_id, destination_key)
    if delivery_id is None:
        return 0
    briefing = build_telegram_briefing(snapshot, publication_date, web_url)
    message_ids: list[str] = []
    try:
        message_ids.extend(provider.send_message(message) for message in briefing.messages)
        if briefing.digest_url:
            message_ids.append(provider.send_document(briefing.digest_url, "오늘 정리본 PDF"))
        complete_telegram_delivery(database_url, delivery_id, message_ids)
        return len(message_ids)
    except Exception as error:
        fail_telegram_delivery(database_url, delivery_id, type(error).__name__)
        raise
