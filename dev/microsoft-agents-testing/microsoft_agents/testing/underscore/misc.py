import re
from .underscore import Underscore, OperationType
from .builtin_wrappers import _make_check


def _safe_attr(x, path, default):
    """Helper for nested attribute access."""
    for name in path:
        if x is None:
            return default
        x = getattr(x, name, None)
    return x if x is not None else default


# Regex matching
_match = _make_check(
    lambda pattern, flags=0: lambda x: bool(re.search(pattern, x, flags)),
    "_match"
)

# Safe nested attribute access
_attr = _make_check(
    lambda *path, default=None: lambda x: _safe_attr(x, path, default),
    "_attr"
)


# Predicate combinators
_all = _make_check(
    lambda *preds: lambda x: all(p(x) if callable(p) else p for p in preds),
    "_all"
)

_any = _make_check(
    lambda *preds: lambda x: any(p(x) if callable(p) else p for p in preds),
    "_any"
)

_between = _make_check(
    lambda low, high: lambda x: low <= x <= high,
    "_between"
)