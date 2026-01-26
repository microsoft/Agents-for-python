# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import random
from typing import TypeVar, Iterable, Callable, Any, Self
from pydantic import BaseModel

from .quantifier import (
    Quantifier,
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
)

from .engine import (
    CheckEngine,
)

T = TypeVar("T", bound=BaseModel)

class Check:
    """
    Unified selection and assertion for models.

    Usage:
        # Select + Assert
        Check(responses).where(type="message").that(text="Hello")

        # Just select (returns item)
        msg = Check(responses).where(type="message").first()

        # Assert on all TODO
        Check(responses).where(type="message").that(text="~Hello") # all messages contain "Hello"

        # Assert any matches
        Check(responses).for_any().that(type="typing")

        # Complex assertions
        Check(responses).where(type="message").last().that(
            text="~confirmed",
            attachments=lambda a: len(a) > 0,
        )
    """

    def __init__(
            self,
            items: Iterable[dict | BaseModel],
        ) -> None:
        self._items = list(items)
        self._engine = CheckEngine()

    def _child(self, items: Iterable[dict | BaseModel]) -> Check:
        """Create a child Check with new items, inheriting selector and quantifier."""
        child = Check(items)
        child._engine = self._engine
        return child

    ###
    ### Selectors
    ###

    def where(self, _filter: dict | Callable | None = None, **kwargs) -> Check:
        """Filter items by criteria. Chainable."""
        res, msgs = zip(*self._check(_filter, **kwargs))
        return self._child(
            [item for item, match in zip(self._items, res) if match],
        )
    
    def where_not(self, _filter: dict | Callable | None = None, **kwargs) -> Check:
        """Exclude items by criteria. Chainable."""
        res, msgs = zip(*self._check(_filter, **kwargs))
        return self._child(
            [item for item, match in zip(self._items, res) if not match],
        )
    
    def order_by(self, key: str | Callable, reverse: bool = False, **kwargs) -> Check:

        """Order items by a specific key or callable. Chainable."""
        if callable(key):
            sort_key = key
        else:
            sort_key = lambda item: item[key] if isinstance(item, dict) else getattr(item, key, None)
        
        return self._child(
            sorted(
                self._items,
                key=sort_key,
                reverse=reverse,
            )
        )
    
    def merge(self, other: Check) -> Check:
        """Merge with another Check's items."""
        return self._child(self._items + other._items)
    
    def _bool_list(self) -> list[bool]:
        return [ True for _ in self._items ]
    
    def first(self, n: int = 1) -> Check:
        """Select the first n items."""
        return self._child(self._items[:n])
    
    def last(self, n: int = 1) -> Check:
        """Select the last n items."""
        return self._child(self._items[-n:])
    
    def at(self, n: int) -> Check:
        """Set selector to 'exactly n'."""
        return self._child(self._items[n:n+1])
    
    def sample(self, n: int) -> Check:
        """Randomly sample n items."""
        if n < 0:
            raise ValueError("Sample size n must be non-negative.")
        
        n = min(n, len(self._items))
        return self._child(random.sample(self._items, n))
    
    ###
    ### Assertion
    ###

    def _that(self, _quantifier: Quantifier, _assert: dict | Callable | None = None, **kwargs) -> bool:
        """Assert that selected items match criteria."""
        res, msgs = zip(*self._check(_assert, **kwargs))
        assert _quantifier(res)
    
    def that(self, _assert: dict | Callable | None = None, **kwargs) -> None:
        """Assert that selected items match criteria."""
        self._that(for_all, _assert, **kwargs)

    def that_for_any(self, _assert: dict | Callable | None = None, **kwargs) -> None:
        """Assert that any selected items match criteria."""
        self._that(for_any, _assert, **kwargs)

    def that_for_all(self, _assert: dict | Callable | None = None, **kwargs) -> None:
        """Assert that all selected items match criteria."""
        self._that(for_all, _assert, **kwargs)

    def that_for_none(self, _assert: dict | Callable | None = None, **kwargs) -> None:
        """Assert that no selected items match criteria."""
        self._that(for_none, _assert, **kwargs)

    def that_for_one(self, _assert: dict | Callable | None = None, **kwargs) -> None:
        """Assert that exactly one selected item matches criteria."""
        self._that(for_one, _assert, **kwargs)
    
    def that_for_exactly(self, _n: int, _assert: dict | Callable | None = None, **kwargs) -> None:
        """Assert that exactly n selected items match criteria."""
        self._that(for_n(_n), _assert, **kwargs)

    def is_empty(self) -> None:
        """Assert that no items are selected."""
        assert len(self._items) == 0, f"Expected no items, found {len(self._items)}."
    
    def is_not_empty(self) -> None:
        """Assert that some items are selected."""
        assert len(self._items) > 0, "Expected some items, found none."
    
    ###
    ### TERMINAL OPERATIONS
    ###

    def get(self) -> list[dict | BaseModel]:
        """Get the selected items as a list."""
        return self._items
    
    def count(self) -> int:
        """Get the count of selected items."""
        return len(self._items)
    
    def empty(self) -> bool:
        """Check if no items are selected."""
        return len(self._items) == 0

    ###
    ### INTERNAL HELPERS
    ###

    def _check(self, _assert: dict | Callable | None = None, **kwargs) -> list[[str, tuple]]:
        baseline = {**(_assert if isinstance(_assert, dict) else {}), **kwargs}
        if callable(_assert):
            # TODO
            baseline["__check_predicate"] = _assert

        return [self._engine.check_verbose(item, baseline) for item in self._items]