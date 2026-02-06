# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the quantifier functions."""

import pytest

from microsoft_agents.testing.core.fluent.backend.quantifier import (
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
    Quantifier,
)


class TestForAll:
    """Tests for the for_all quantifier."""

    def test_for_all_empty_list(self):
        """for_all returns True for an empty list (vacuous truth)."""
        assert for_all([]) is True

    def test_for_all_all_true(self):
        """for_all returns True when all items are True."""
        assert for_all([True, True, True]) is True

    def test_for_all_all_false(self):
        """for_all returns False when all items are False."""
        assert for_all([False, False, False]) is False

    def test_for_all_mixed(self):
        """for_all returns False when any item is False."""
        assert for_all([True, False, True]) is False

    def test_for_all_single_true(self):
        """for_all returns True for a single True item."""
        assert for_all([True]) is True

    def test_for_all_single_false(self):
        """for_all returns False for a single False item."""
        assert for_all([False]) is False


class TestForAny:
    """Tests for the for_any quantifier."""

    def test_for_any_empty_list(self):
        """for_any returns False for an empty list."""
        assert for_any([]) is False

    def test_for_any_all_true(self):
        """for_any returns True when all items are True."""
        assert for_any([True, True, True]) is True

    def test_for_any_all_false(self):
        """for_any returns False when all items are False."""
        assert for_any([False, False, False]) is False

    def test_for_any_mixed(self):
        """for_any returns True when at least one item is True."""
        assert for_any([False, True, False]) is True

    def test_for_any_single_true(self):
        """for_any returns True for a single True item."""
        assert for_any([True]) is True

    def test_for_any_single_false(self):
        """for_any returns False for a single False item."""
        assert for_any([False]) is False


class TestForNone:
    """Tests for the for_none quantifier."""

    def test_for_none_empty_list(self):
        """for_none returns True for an empty list."""
        assert for_none([]) is True

    def test_for_none_all_true(self):
        """for_none returns False when all items are True."""
        assert for_none([True, True, True]) is False

    def test_for_none_all_false(self):
        """for_none returns True when all items are False."""
        assert for_none([False, False, False]) is True

    def test_for_none_mixed(self):
        """for_none returns False when any item is True."""
        assert for_none([False, True, False]) is False

    def test_for_none_single_true(self):
        """for_none returns False for a single True item."""
        assert for_none([True]) is False

    def test_for_none_single_false(self):
        """for_none returns True for a single False item."""
        assert for_none([False]) is True


class TestForOne:
    """Tests for the for_one quantifier."""

    def test_for_one_empty_list(self):
        """for_one returns False for an empty list."""
        assert for_one([]) is False

    def test_for_one_all_true(self):
        """for_one returns False when all items are True (more than one)."""
        assert for_one([True, True, True]) is False

    def test_for_one_all_false(self):
        """for_one returns False when all items are False."""
        assert for_one([False, False, False]) is False

    def test_for_one_exactly_one_true(self):
        """for_one returns True when exactly one item is True."""
        assert for_one([False, True, False]) is True

    def test_for_one_two_true(self):
        """for_one returns False when two items are True."""
        assert for_one([True, True, False]) is False

    def test_for_one_single_true(self):
        """for_one returns True for a single True item."""
        assert for_one([True]) is True

    def test_for_one_single_false(self):
        """for_one returns False for a single False item."""
        assert for_one([False]) is False


class TestForN:
    """Tests for the for_n quantifier factory."""

    def test_for_n_zero_empty_list(self):
        """for_n(0) returns True for an empty list."""
        assert for_n(0)([]) is True

    def test_for_n_zero_all_false(self):
        """for_n(0) returns True when all items are False."""
        assert for_n(0)([False, False, False]) is True

    def test_for_n_zero_some_true(self):
        """for_n(0) returns False when any item is True."""
        assert for_n(0)([False, True, False]) is False

    def test_for_n_one_exactly_one_true(self):
        """for_n(1) returns True when exactly one item is True."""
        assert for_n(1)([False, True, False]) is True

    def test_for_n_one_two_true(self):
        """for_n(1) returns False when two items are True."""
        assert for_n(1)([True, True, False]) is False

    def test_for_n_two_exactly_two_true(self):
        """for_n(2) returns True when exactly two items are True."""
        assert for_n(2)([True, True, False]) is True

    def test_for_n_two_three_true(self):
        """for_n(2) returns False when three items are True."""
        assert for_n(2)([True, True, True]) is False

    def test_for_n_three_all_true(self):
        """for_n(3) returns True when exactly three items are True."""
        assert for_n(3)([True, True, True]) is True

    def test_for_n_returns_callable(self):
        """for_n returns a callable quantifier."""
        quantifier = for_n(2)
        assert callable(quantifier)

    def test_for_n_can_be_reused(self):
        """for_n quantifier can be reused on multiple lists."""
        for_two = for_n(2)
        assert for_two([True, True, False]) is True
        assert for_two([True, False, False]) is False
        assert for_two([True, True, True, False]) is False
        assert for_two([False, True, True, False]) is True


class TestQuantifierProtocol:
    """Tests for the Quantifier protocol compatibility."""

    def test_for_all_matches_protocol(self):
        """for_all can be used as a Quantifier."""
        quantifier: Quantifier = for_all
        assert quantifier([True, True]) is True

    def test_for_any_matches_protocol(self):
        """for_any can be used as a Quantifier."""
        quantifier: Quantifier = for_any
        assert quantifier([False, True]) is True

    def test_for_none_matches_protocol(self):
        """for_none can be used as a Quantifier."""
        quantifier: Quantifier = for_none
        assert quantifier([False, False]) is True

    def test_for_one_matches_protocol(self):
        """for_one can be used as a Quantifier."""
        quantifier: Quantifier = for_one
        assert quantifier([False, True, False]) is True

    def test_for_n_result_matches_protocol(self):
        """for_n result can be used as a Quantifier."""
        quantifier: Quantifier = for_n(2)
        assert quantifier([True, True, False]) is True
