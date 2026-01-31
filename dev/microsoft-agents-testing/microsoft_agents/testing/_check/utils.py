from typing import Callable

def format_filter(_filter: str | dict | Callable | None, **kwargs) -> str:
    """Format the filter for display in exception messages."""
    if _filter is None:
        return "no filter"
    if isinstance(_filter, dict):
        combined = {**_filter, **kwargs}
        return f"dict {combined}"
    if callable(_filter):
        return f"callable {_filter.__name__} with args {kwargs}"
    return str(_filter)