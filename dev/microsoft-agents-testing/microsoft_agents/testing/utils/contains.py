# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Contains predicate helper for fluent test assertions."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any, cast

from pydantic import BaseModel

from microsoft_agents.testing.core.fluent.backend import ModelPredicate

PredicateFilter = Callable[[Any], bool] | dict[str, Any]
_EMPTY_FILTER = cast(PredicateFilter, object())


def _to_snake_case(value: str) -> str:
    value = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", value).lower()


def _normalize_dict_keys(value: Any) -> Any:
    if isinstance(value, dict):
        normalized = {}
        for key, item in value.items():
            normalized_key = _to_snake_case(key) if isinstance(key, str) else key
            normalized[normalized_key] = _normalize_dict_keys(item)
        return normalized
    if isinstance(value, list):
        return [_normalize_dict_keys(item) for item in value]
    return value


def _build_predicate(
    _filter: PredicateFilter = _EMPTY_FILTER,
    **kwargs,
) -> Callable[[Any], bool]:
    """Build the value predicate used while traversing nested values.

    :param _filter: A callable predicate or dictionary of field checks.
    :param kwargs: Additional field checks merged with a dictionary filter.
    :raises ValueError: If no filter or keyword checks are provided, or if the
        filter is ``None``.
    :return: A callable that evaluates one traversed value.
    """
    if _filter is None:
        raise ValueError("Filter cannot be None.")
    if _filter is _EMPTY_FILTER or (isinstance(_filter, dict) and not _filter):
        if not kwargs:
            raise ValueError("A filter or keyword criteria must be provided.")
        _filter = {}

    if callable(_filter) and not kwargs:
        return _filter

    model_predicate = ModelPredicate.from_args(_filter, **kwargs)

    def predicate(value: Any) -> bool:
        if isinstance(value, list):
            return False

        try:
            if any(model_predicate.eval(value).result_bools):
                return True
            if isinstance(value, BaseModel):
                field_name_value = value.model_dump(
                    exclude_unset=True,
                    exclude_none=True,
                    by_alias=False,
                )
                return any(model_predicate.eval(field_name_value).result_bools)
            if isinstance(value, dict):
                normalized_value = _normalize_dict_keys(value)
                if normalized_value != value:
                    return any(model_predicate.eval(normalized_value).result_bools)
            return False
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            return False

    return predicate


class Contains:
    """Callable predicate that searches nested model, dict, and iterable values."""

    def __init__(self, _filter: PredicateFilter = _EMPTY_FILTER, **kwargs) -> None:
        """Initialize the predicate with the same criteria accepted by ``contains``.

        ``_filter`` may be a callable applied to each visited value or a
        dictionary of field checks evaluated against each visited model or dict.
        Keyword checks are merged with dictionary filters, with keyword values
        taking precedence for duplicate keys. A filter or keyword criteria must
        be provided.

        :param _filter: A callable predicate or dictionary of field checks.
        :param kwargs: Additional field checks.
        :raises ValueError: If no criteria are provided, the filter is ``None``,
            or the filter type is invalid.
        """
        self._predicate = _build_predicate(_filter, **kwargs)
        self._max_depth = 3

    def __call__(self, x: Any) -> bool:
        return self._contains(x)

    def depth(self, depth: int) -> Contains:
        """Return a new predicate with a different maximum search depth.

        Depth starts at the root value as ``0``. Nested model fields, dict
        values, and iterable items increment the depth by one.

        :param depth: The maximum depth to search.
        :raises ValueError: If ``depth`` is negative.
        :return: A new ``Contains`` instance with the requested depth.
        """
        if depth < 0:
            raise ValueError("Depth must be non-negative.")
        contains = Contains(self._predicate)
        contains._max_depth = depth
        return contains

    def _contains(self, x: Any, depth: int = 0) -> bool:
        if depth > self._max_depth:
            return False

        try:
            if self._predicate(x):
                return True
        except (AttributeError, IndexError, KeyError, TypeError):
            pass

        if depth == self._max_depth:
            return False

        if isinstance(x, BaseModel):
            it = (value for _, value in x)
        elif isinstance(x, dict):
            it = x.values()
        elif isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            it = x
        else:
            return False

        return any(self._contains(value, depth + 1) for value in it)


def contains(
    _filter: PredicateFilter = _EMPTY_FILTER,
    **kwargs,
) -> Contains:
    """Create a predicate that searches nested model, dict, and iterable values.

    A filter or keyword criteria must be provided.

    :param _filter: A callable predicate or dictionary of field checks.
    :param kwargs: Additional field checks.
    :raises ValueError: If no criteria are provided, the filter is ``None``, or
        the filter type is invalid.
    :return: A ``Contains`` predicate.
    """
    return Contains(_filter, **kwargs)
