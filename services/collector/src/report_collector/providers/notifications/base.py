from typing import Protocol


class NotificationProvider(Protocol):
    def send_message(self, html: str) -> str: ...

    def send_document(self, document_url: str, caption: str) -> str: ...
