from pathlib import Path
from urllib.parse import quote

import httpx


class SupabaseDigestStorage:
    def __init__(self, base_url: str, service_key: str, bucket: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_key = service_key
        self.bucket = bucket

    def upload(self, source: Path, object_path: str) -> str:
        encoded_path = quote(object_path, safe="/")
        endpoint = f"{self.base_url}/storage/v1/object/{self.bucket}/{encoded_path}"
        headers = {
            "authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
            "content-type": "application/pdf",
            "x-upsert": "true",
        }
        with source.open("rb") as content:
            response = httpx.put(endpoint, headers=headers, content=content, timeout=60)
        response.raise_for_status()
        return f"{self.base_url}/storage/v1/object/public/{self.bucket}/{encoded_path}"
