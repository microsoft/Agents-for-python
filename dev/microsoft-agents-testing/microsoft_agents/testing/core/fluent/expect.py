# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Callable, Iterable, Self, TypeVar

from pydantic import BaseModel

from .backend import (
    ModelPredicate,
    Quantifier,
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
)
from .backend.describe import Describe

ModelT = TypeVar("ModelT", bound=dict | BaseModel)


class Expect:
    """
    Assertion class that raises on failure.
    
    Extends Check with throwing assertion methods. Use Select to filter
    items before passing to Expect.

    Usage:
        # Assert all items match
        Expect(responses).that(type="message")

        # Assert any item matches
        Expect(responses).that_for_any(text="hello")

        # Assert count
        Expect(responses).has_count(3)

        # Chain with Select
        Select(responses).where(type="message").expect.that(text="hello")
    """

    def __init__(self, items: Iterable[ModelT]) -> None:
        """Initialize Expect with a collection of items.
        
        :param items: An iterable of dicts or BaseModel instances.
        """
        self._items = list(items)
        self._describer = Describe()

    # =========================================================================
    # Assertions with Quantifiers
    # =========================================================================

    def that(self, _assert: dict | Callable | None = None, **kwargs) -> Self:
        """Assert that ALL items match criteria.
        
        :param _assert: A dict of field checks or a callable predicate.
        :param kwargs: Additional field checks.
        :raises AssertionError: If not all items match.
        :return: Self for chaining.
        """
        return self._assert_with(for_all, _assert, **kwargs)

    def that_for_any(self, _assert: dict | Callable | None = None, **kwargs) -> Self:
        """Assert that ANY item matches criteria.
        
        :param _assert: A dict of field checks or a callable predicate.
        :param kwargs: Additional field checks.
        :raises AssertionError: If no items match.
        :return: Self for chaining.
        """
        return self._assert_with(for_any, _assert, **kwargs)

    def that_for_all(self, _assert: dict | Callable | None = None, **kwargs) -> Self:
        """Assert that ALL items match criteria.
        
        :param _assert: A dict of field checks or a callable predicate.
        :param kwargs: Additional field checks.
        :raises AssertionError: If not all items match.
        :return: Self for chaining.
        """
        return self._assert_with(for_all, _assert, **kwargs)

    def that_for_none(self, _assert: dict | Callable | None = None, **kwargs) -> Self:
        """Assert that NO items match criteria.
        
        :param _assert: A dict of field checks or a callable predicate.
        :param kwargs: Additional field checks.
        :raises AssertionError: If any items match.
        :return: Self for chaining.
        """
        return self._assert_with(for_none, _assert, **kwargs)

    def that_for_one(self, _assert: dict | Callable | None = None, **kwargs) -> Self:
        """Assert that EXACTLY ONE item matches criteria.
        
        :param _assert: A dict of field checks or a callable predicate.
        :param kwargs: Additional field checks.
        :raises AssertionError: If not exactly one item matches.
        :return: Self for chaining.
        """
        return self._assert_with(for_one, _assert, **kwargs)

    def that_for_exactly(self, n: int, _assert: dict | Callable | None = None, **kwargs) -> Self:
        """Assert that EXACTLY N items match criteria.
        
        :param n: The exact number of items that should match.
        :param _assert: A dict of field checks or a callable predicate.
        :param kwargs: Additional field checks.
        :raises AssertionError: If not exactly n items match.
        :return: Self for chaining.
        """
        return self._assert_with(for_n(n), _assert, **kwargs)

    def _assert_with(
        self, 
        quantifier: Quantifier, 
        _assert: dict | Callable | None = None, 
        **kwargs
    ) -> Self:
        """Internal: assert items match criteria using the given quantifier.
        
        :param quantifier: The quantifier to use for evaluation.
        :param _assert: A dict of field checks or a callable predicate.
        :param kwargs: Additional field checks.
        :raises AssertionError: If the assertion fails.
        :return: Self for chaining.
        """
        mp = ModelPredicate.from_args(_assert, **kwargs)
        result = mp.eval(self._items)
        passed = quantifier(result.result_bools)

        if not passed:
            description = self._describer.describe(result, quantifier)
            failures = self._describer.describe_failures(result)
            failure_details = "\n  ".join(failures) if failures else "No details available."
            
            raise AssertionError(
                f"Expectation failed:\n"
                f"  {description}\n"
                f"  Details:\n  {failure_details}"
            )

        return self

    # =========================================================================
    # Count Assertions
    # =========================================================================

    def is_empty(self) -> Self:
        """Assert that no items exist.
        
        :raises AssertionError: If there are any items.
        :return: Self for chaining.
        """
        if len(self._items) != 0:
            raise AssertionError(f"Expected no items, found {len(self._items)}.")
        return self

    def is_not_empty(self) -> Self:
        """Assert that some items exist.
        
        :raises AssertionError: If there are no items.
        :return: Self for chaining.
        """
        if len(self._items) == 0:
            raise AssertionError("Expected some items, found none.")
        return self