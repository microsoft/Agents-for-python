from urllib.parse import urlsplit

from a2a.types import AgentInterface


def _get_interface_route_path(interface: AgentInterface) -> str:
    parsed = urlsplit(interface.url)

    if parsed.query or parsed.fragment:
        raise ValueError(
            "Agent interface URLs cannot contain a query string or fragment."
        )

    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"Invalid HTTP agent interface URL: {interface.url}")
        path = parsed.path
    else:
        path = parsed.path

    if not path.startswith("/"):
        raise ValueError("Relative agent interface URLs must start with '/'.")

    return path.rstrip("/") or "/"
