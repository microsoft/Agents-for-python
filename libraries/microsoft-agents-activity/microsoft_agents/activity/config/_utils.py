# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ._engine import _Path, _SimplePathSegment, _Wildcard, _PathSegment


def _get_segments(*segments: str | int | _PathSegment, **kwargs) -> list[_PathSegment]:
    """Wrap string/int keys, leaving existing segment objects unchanged."""
    return [
        (
            segment
            if isinstance(segment, _PathSegment)
            else _SimplePathSegment(segment, **kwargs)
        )
        for segment in segments
    ]


def _legpath(*segments: str | int | _PathSegment) -> _Path:
    """Create a path that ignores case and underscores in string keys.

    Existing segment objects keep their own matching rules. Pass ``wildcard()``
    explicitly to enumerate dictionary keys.
    """
    return _Path(*_get_segments(*segments, ignore_case=True, ignore_underscores=True))


def _netpath(*segments: str | int | _PathSegment) -> _Path:
    """Create a path that ignores case but keeps underscores significant.

    Existing segment objects keep their own matching rules. Pass ``wildcard()``
    explicitly to enumerate dictionary keys.
    """
    return _Path(*_get_segments(*segments, ignore_case=True, ignore_underscores=False))


def wildcard() -> _PathSegment:
    """Match every key at one dictionary level in a collection path.

    Use with ``Configuration.collect``, ``collect_str``, or ``get_sections``.
    Ordinary strings, including ``"*"`` itself, remain literal keys.
    Wildcards do not enumerate list positions and are not accepted by
    single-value getters or assignment.

    Example::

        >>> from microsoft_agents.activity.config import Configuration, wildcard
        >>> config = Configuration({"ports": {"first": 3978, "second": 3979}})
        >>> config.collect(["ports", wildcard()])
        [3978, 3979]
    """
    return _Wildcard()
