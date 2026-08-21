from dataclasses import dataclass, field


@dataclass
class MockNotificationProvider:
    messages: list[str] = field(default_factory=list)
    documents: list[tuple[str, str]] = field(default_factory=list)

    def send_message(self, html: str) -> str:
        self.messages.append(html)
        return str(len(self.messages))

    def send_document(self, document_url: str, caption: str) -> str:
        self.documents.append((document_url, caption))
        return f"document-{len(self.documents)}"
