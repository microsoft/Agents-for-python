from __future__ import annotations

from typing import TypeVar, Iterable, Callable
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
            quantifier: Quantifier = for_all,
        ) -> None:
        self._items = list(items)
        self._quantifier: Quantifier = quantifier
        self._engine = CheckEngine()

    def _child(self, items: Iterable[dict | BaseModel], quantifier: Quantifier | None = None) -> Check:
        """Create a child Check with new items, inheriting selector and quantifier."""
        child = Check(items, quantifier or self._quantifier)
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
            self._quantifier
        )
    
    def where_not(self, _filter: dict | Callable | None = None, **kwargs) -> Check:
        """Exclude items by criteria. Chainable."""
        res, msgs = zip(*self._check(_filter, **kwargs))
        return self._child(
            [item for item, match in zip(self._items, res) if not match],
            self._quantifier
        )
    
    def merge(self, other: Check) -> Check:
        """Merge with another Check's items."""
        return self._child(self._items + other._items, self._quantifier)
    
    def _bool_list(self) -> list[bool]:
        return [ True for _ in self._items ]
    
    def first(self) -> Check:
        """Select the first item."""
        return self._child(self._items[:1])
    
    def last(self) -> Check:
        """Select the last item."""
        return self._child(self._items[-1:])
    
    def at(self, n: int) -> Check:
        """Set selector to 'exactly n'."""
        return self._child(self._items[n:n+1])
    
    def cap(self, n: int) -> Check:
        """Limit selection to first n items."""
        return self._child(self._items[:n])
    
    ###
    ### Quantifiers
    ###
    
    def for_any(self) -> Check:
        """Set selector to 'any'."""
        return self._child(self._items, for_any)

    def for_all(self) -> Check:
        """Set selector to 'all'."""
        return self._child(self._items, for_all)

    def for_none(self) -> Check:
        """Set selector to 'none'."""
        return self._child(self._items, for_none)
    
    def for_one(self) -> Check:
        """Set selector to 'one'."""
        return self._child(self._items, for_one)
    
    def for_exactly(self, n: int) -> Check:
        """Set selector to 'exactly n'."""
        return self._child(self._items, for_n(n))
    
    ###
    ### Assertion
    ###
    
    def that(self, _assert: dict | Callable | None = None, **kwargs) -> bool:
        """Assert that selected items match criteria."""
        res, msgs = zip(*self._check(_assert, **kwargs))
        assert self._quantifier(res), msgs
    
    def count_is(self, n: int) -> bool:
        """Check if the count of selected items is exactly n."""
        return len(self._items) == n
    
    ###
    ### TERMINAL OPERATIONS
    ###

    def get(self) -> list[dict | BaseModel]:
        """Get the selected items as a list."""
        return self._items
    
    def get_one(self) -> dict | BaseModel:
        """Get a single selected item. Raises if not exactly one."""
        if len(self._items) != 1:
            raise ValueError(f"Expected exactly one item, found {len(self._items)}.")
        return self._items[0]
    
    def count(self) -> int:
        """Get the count of selected items."""
        return len(self._items)
    
    def exists(self) -> bool:
        """Check if any selected items exist."""
        return len(self._items) > 0
    
    ###
    ### INTERNAL HELPERS
    ###

    def _check(self, _assert: dict | Callable | None = None, **kwargs) -> list[[str, tuple]]:
        baseline = {**(_assert if isinstance(_assert, dict) else {}), **kwargs}
        if callable(_assert):
            # TODO
            baseline["__Check__predicate__"] = _assert

        return [self._engine.check_verbose(item, baseline) for item in self._items]
        