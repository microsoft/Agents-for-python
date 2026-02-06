# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Quantifier functions for predicate evaluation.

Quantifiers determine how boolean results from multiple items are combined
to produce a final pass/fail result (e.g., all must match, any must match).
"""

from typing import Protocol


class Quantifier(Protocol):
    """Protocol for quantifier functions.
    
    A quantifier takes a list of boolean results and returns whether
    the overall assertion passes based on its logic (all, any, none, etc.).
    """
    
    @staticmethod
    def __call__(items: list[bool]) -> bool:
        ...

def for_all(items: list[bool]) -> bool:
    """Return True if all items are True."""
    return all(items)


def for_any(items: list[bool]) -> bool:
    """Return True if any item is True."""
    return any(items)


def for_none(items: list[bool]) -> bool:
    """Return True if no items are True."""
    return all(not item for item in items)


def for_one(items: list[bool]) -> bool:
    """Return True if exactly one item is True."""
    return sum(1 for item in items if item) == 1


def for_n(n: int) -> Quantifier:
    """Return a quantifier that passes if exactly n items are True.
    
    :param n: The exact number of True values required.
    :return: A quantifier function.
    """
    def _for_n(items: list[bool]) -> bool:
        return sum(1 for item in items if item) == n
    return _for_n