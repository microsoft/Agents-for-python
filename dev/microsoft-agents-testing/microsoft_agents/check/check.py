from __future__ import annotations

from typing import Protocol, TypeVar, Iterable, overload, Callable
from pydantic import BaseModel
from strenum import StrEnum

from .quantifier import (
    Quantifier,
    for_all,
    for_any,
    for_one,
    for_none,
    for_exactly,
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
        Check(responses).any().that(type="typing")

        # Complex assertions
        Check(responses).where(type="message").last.that(
            text="~confirmed",
            attachments=lambda a: len(a) > 0,
        )
    """

    def __init__(self, items: Iterable[dict | BaseModel], quantifier: Quantifier = for_all) -> None:
        self._items = list(items)
        self._quantifier: Quantifier = quantifier

    ###
    ### Selectors
    ###

    def where(self, _filter: dict | Callable | None = None, **kwargs) -> Check:
        """Filter items by criteria. Chainable."""

        if not isinstance(_filter, (dict, Callable, type(None))): # TODO -> checking callable
            raise TypeError("Filter must be a dict, callable, or None.")

        query = {**(_filter if isinstance(_filter, dict) else {}), **kwargs}
        predicate = _filter if callable(_filter) else None

        filtered = []
        for item in self._selected:
            if self._matches(item, query, predicate):
                filtered.append(item)
        
        self._selected = filtered
        return self
    
    def first(self) -> Check:
        """Select the first item."""
        if not self._items:
            raise ValueError("No items to select from.")
        return Check(self._items[:1], self._selector)
    
    def last(self) -> Check:
        """Select the last item."""
        if not self._items:
            raise ValueError("No items to select from.")
        return Check(self._items[-1:], self._selector)
    
    def at(self, n: int) -> Check:
        """Set selector to 'exactly n'."""
        new_n = n
        if n < 0:
            new_n = len(self._items) + n
        if new_n >= len(self._items):
            raise ValueError(f"Index {n} out of range for items of length {len(self._items)}.")
        return Check(self._items[new_n:new_n+1], self._quantifier)
    
    ###
    ### Quantifiers
    ###
    
    def any(self) -> Check:
        """Set selector to 'any'."""
        return Check(self._items, for_any)

    def all(self) -> Check:
        """Set selector to 'all'."""
        return Check(self._items, for_all)

    def none(self) -> Check:
        """Set selector to 'none'."""
        return Check(self._items, for_none)
    
    def one(self) -> Check:
        """Set selector to 'one'."""
        return Check(self._items, for_one)
    
    ###
    ### Assertion
    ###
    
    def that(self, _assert: dict | Callable | None = None, **kwargs) -> bool:
        """Assert that selected items match criteria."""

        if not isinstance(_assert, (dict, Callable, type(None))): # TODO -> checking callable
            raise TypeError("Assert must be a dict, callable, or None.")

        query = {**(_assert if isinstance(_assert, dict) else {}), **kwargs}
        predicate = _assert if callable(_assert) else None

        def item_predicate(item: dict | BaseModel) -> bool:
            return self._matches(item, query, predicate)

        return self._selector(self._selected, item_predicate)
    
    def count_is(self, n: int) -> bool:
        """Check if the count of selected items is exactly n."""
        return len(self._selected) == n
    
    ###
    ### TERMINAL OPERATIONS
    ###

    def get(self) -> list[dict | BaseModel]:
        """Get the selected items as a list."""
        return self._selected
    
    def get_one(self) -> dict | BaseModel:
        """Get a single selected item. Raises if not exactly one."""
        if len(self._selected) != 1:
            raise ValueError(f"Expected exactly one item, found {len(self._selected)}.")
        return self._selected[0]
    
    def count(self) -> int:
        """Get the count of selected items."""
        return len(self._selected)
    
    def exists(self) -> bool:
        """Check if any selected items exist."""
        return len(self._selected) > 0
    
    ###
    ### INTERNAL HELPERS
    ###

    