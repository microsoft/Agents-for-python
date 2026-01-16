import pytest
from microsoft_agents.testing.check.quantifier import (
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
    Quantifier,
)


class TestForAll:
    def test_all_true_returns_true(self):
        assert for_all([True, True, True]) is True

    def test_all_false_returns_false(self):
        assert for_all([False, False, False]) is False

    def test_mixed_returns_false(self):
        assert for_all([True, False, True]) is False

    def test_empty_list_returns_true(self):
        assert for_all([]) is True

    def test_single_true_returns_true(self):
        assert for_all([True]) is True

    def test_single_false_returns_false(self):
        assert for_all([False]) is False


class TestForAny:
    def test_all_true_returns_true(self):
        assert for_any([True, True, True]) is True

    def test_all_false_returns_false(self):
        assert for_any([False, False, False]) is False

    def test_mixed_returns_true(self):
        assert for_any([False, True, False]) is True

    def test_empty_list_returns_false(self):
        assert for_any([]) is False

    def test_single_true_returns_true(self):
        assert for_any([True]) is True

    def test_single_false_returns_false(self):
        assert for_any([False]) is False


class TestForNone:
    def test_all_true_returns_false(self):
        assert for_none([True, True, True]) is False

    def test_all_false_returns_true(self):
        assert for_none([False, False, False]) is True

    def test_mixed_returns_false(self):
        assert for_none([True, False, True]) is False

    def test_empty_list_returns_true(self):
        assert for_none([]) is True

    def test_single_true_returns_false(self):
        assert for_none([True]) is False

    def test_single_false_returns_true(self):
        assert for_none([False]) is True


class TestForOne:
    def test_exactly_one_true_returns_true(self):
        assert for_one([False, True, False]) is True

    def test_multiple_true_returns_false(self):
        assert for_one([True, True, False]) is False

    def test_all_true_returns_false(self):
        assert for_one([True, True, True]) is False

    def test_all_false_returns_false(self):
        assert for_one([False, False, False]) is False

    def test_empty_list_returns_false(self):
        assert for_one([]) is False

    def test_single_true_returns_true(self):
        assert for_one([True]) is True

    def test_single_false_returns_false(self):
        assert for_one([False]) is False


class TestForN:
    def test_for_n_zero_with_all_false_returns_true(self):
        quantifier = for_n(0)
        assert quantifier([False, False, False]) is True

    def test_for_n_zero_with_any_true_returns_false(self):
        quantifier = for_n(0)
        assert quantifier([True, False, False]) is False

    def test_for_n_two_with_exactly_two_true_returns_true(self):
        quantifier = for_n(2)
        assert quantifier([True, True, False]) is True

    def test_for_n_two_with_one_true_returns_false(self):
        quantifier = for_n(2)
        assert quantifier([True, False, False]) is False

    def test_for_n_two_with_three_true_returns_false(self):
        quantifier = for_n(2)
        assert quantifier([True, True, True]) is False

    def test_for_n_returns_callable(self):
        quantifier = for_n(3)
        assert callable(quantifier)

    def test_for_n_with_empty_list_returns_true_for_zero(self):
        quantifier = for_n(0)
        assert quantifier([]) is True

    def test_for_n_with_empty_list_returns_false_for_nonzero(self):
        quantifier = for_n(1)
        assert quantifier([]) is False

    def test_for_n_large_number(self):
        quantifier = for_n(5)
        assert quantifier([True] * 5 + [False] * 5) is True
        assert quantifier([True] * 4 + [False] * 6) is False


class TestQuantifierProtocol:
    def test_for_all_matches_protocol(self):
        quantifier: Quantifier = for_all
        assert quantifier([True, True]) is True

    def test_for_any_matches_protocol(self):
        quantifier: Quantifier = for_any
        assert quantifier([True, False]) is True

    def test_for_none_matches_protocol(self):
        quantifier: Quantifier = for_none
        assert quantifier([False, False]) is True

    def test_for_one_matches_protocol(self):
        quantifier: Quantifier = for_one
        assert quantifier([True, False]) is True

    def test_for_n_returns_protocol_compatible(self):
        quantifier: Quantifier = for_n(2)
        assert quantifier([True, True, False]) is True