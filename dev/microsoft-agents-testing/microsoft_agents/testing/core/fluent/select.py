# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import random
from typing import TypeVar, Iterable, Callable, cast
from pydantic import BaseModel

from .backend import (
    for_all,
    ModelPredicate
)

from .expect import Expect

T = TypeVar("T", bound=BaseModel)

class Select:
    """
    Unified selection and assertion for models.

    Usage:
        # Select + Assert
        Select(responses).where(type="message").that(text="Hello")

        # Just select (returns item)
        msg = Select(responses).where(type="message").first()

        # Assert on all TODO
        Select(responses).where(type="message").that(text="~Hello") # all messages contain "Hello"

        # Assert any matches
        Select(responses).for_any().that(type="typing")

        # Complex assertions
        Select(responses).where(type="message").last().that(
            text="~confirmed",
            attachments=lambda a: len(a) > 0,
        )
    """

    def __init__(
            self,
            items: Iterable[dict] | Iterable[BaseModel],
        ) -> None:
        self._items = cast(list[dict] | list[BaseModel], list(items))

    def expect(self) -> Expect:
        """Get an Expect instance for assertions on the current selection."""
        return Expect(self._items)

    def _child(self, items: Iterable[dict] | Iterable[BaseModel]) -> Select:
        """Create a child Select with new items, inheriting selector and quantifier."""
        child = Select(items)
        return child

    ###
    ### Selectors
    ###

    def _where(self, _filter: dict | Callable | None = None, _reverse: bool=False, **kwargs) -> Select:
        """Filter items by criteria. Chainable."""
        mp = ModelPredicate.from_args(_filter, **kwargs)

        mpr = mp.eval(self._items)
        results = mpr.result_bools
        
        mapping = zip(self._items, results)
        filtered_items = [item for item, keep in mapping if keep != _reverse] # keep if not _reverse else not keep

        return self._child(filtered_items)

    def where(self, _filter: dict | Callable | None = None, **kwargs) -> Select:
        return self._where(_filter, **kwargs)

    def where_not(self, _filter: dict | Callable | None = None, **kwargs) -> Select:
        """Exclude items by criteria. Chainable."""
        return self._where(_filter, _reverse=True, **kwargs)
    
    def order_by(self, key: str | Callable | None, reverse: bool = False, **kwargs) -> Select:
        """Order items by a specific key or callable. Chainable."""

        dt = DictionaryTransform.from_args(key, **kwargs)
        
        return self._child(
            sorted(
                self._items,
                key=dt.eval,
                reverse=reverse,
            )
        )
    
    def merge(self, other: Select) -> Select:
        """Merge with another Select's items."""
        return self._child(self._items + other._items)
    
    def _bool_list(self) -> list[bool]:
        return [ True for _ in self._items ]
    
    def first(self, n: int = 1) -> Select:
        """Select the first n items."""
        return self._child(self._items[:n])
    
    def last(self, n: int = 1) -> Select:
        """Select the last n items."""
        return self._child(self._items[-n:])
    
    def at(self, n: int) -> Select:
        """Set selector to 'exactly n'."""
        return self._child(self._items[n:n+1])
    
    def sample(self, n: int) -> Select:
        """Randomly sample n items."""
        if n < 0:
            raise ValueError("Sample size n must be non-negative.")
        
        n = min(n, len(self._items))
        return self._child(random.sample(self._items, n))
    
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
        """Select if no items are selected."""
        return len(self._items) == 0