import socket
from ipaddress import ip_address
from urllib.parse import urlparse

from report_collector.domain.errors import CollectorError

BLOCKED_HOSTS = {"localhost", "metadata.google.internal"}


def _is_blocked_ip(value: str) -> bool:
    address = ip_address(value)
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
        )
    )


async def ensure_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise CollectorError("Only public HTTP(S) URLs are allowed")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in BLOCKED_HOSTS or hostname.endswith(".local"):
        raise CollectorError("Private or local targets are blocked")
    try:
        if _is_blocked_ip(hostname):
            raise CollectorError("Private or local targets are blocked")
        return
    except ValueError:
        pass
    loop = __import__("asyncio").get_running_loop()
    records = await loop.run_in_executor(None, socket.getaddrinfo, hostname, parsed.port or 443)
    if any(_is_blocked_ip(record[4][0]) for record in records):
        raise CollectorError("Resolved private or local targets are blocked")
