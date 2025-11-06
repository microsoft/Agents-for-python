from urllib.parse import urlparse


def get_host_and_port(url: str) -> tuple[str, int]:
    """Extract host and port from a URL."""

    parsed_url = urlparse(url)
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
    return host, port
