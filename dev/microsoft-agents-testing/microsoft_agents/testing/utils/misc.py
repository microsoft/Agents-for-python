from urllib.parse import urlparse

from microsoft_agents.activity import Activity


def get_host_and_port(url: str) -> tuple[str, int]:
    """Extract host and port from a URL."""

    parsed_url = urlparse(url)
    host = parsed_url.hostname or "localhost"
    port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
    return host, port


def normalize_activity_data(source: Activity | dict) -> dict:
    """Normalize Activity data to a dictionary format."""

    if isinstance(source, Activity):
        return source.model_dump(exclude_unset=True)
    return source
