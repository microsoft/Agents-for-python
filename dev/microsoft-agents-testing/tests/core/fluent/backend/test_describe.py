# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the Describe class."""

import pytest

from microsoft_agents.testing.core.fluent.backend.describe import Describe
from microsoft_agents.testing.core.fluent.backend.model_predicate import ModelPredicateResult
from microsoft_agents.testing.core.fluent.backend.quantifier import (
    for_all,
    for_any,
    for_none,
    for_one,
    for_n,
)


class TestDescribeCountSummary:
    """Tests for the _count_summary method."""

    def test_count_summary_all_true(self):
        """Count summary with all True values."""
        describe = Describe()
        result = describe._count_summary([True, True, True])
        assert result == "3/3 items matched"

    def test_count_summary_all_false(self):
        """Count summary with all False values."""
        describe = Describe()
        result = describe._count_summary([False, False, False])
        assert result == "0/3 items matched"

    def test_count_summary_mixed(self):
        """Count summary with mixed values."""
        describe = Describe()
        result = describe._count_summary([True, False, True])
        assert result == "2/3 items matched"

    def test_count_summary_empty(self):
        """Count summary with empty list."""
        describe = Describe()
        result = describe._count_summary([])
        assert result == "0/0 items matched"


class TestDescribeIndicesSummary:
    """Tests for the _indices_summary method."""

    def test_indices_summary_matched_some(self):
        """Indices summary for matched items."""
        describe = Describe()
        result = describe._indices_summary([True, False, True], matched=True)
        assert result == "[0, 2]"

    def test_indices_summary_failed_some(self):
        """Indices summary for failed items."""
        describe = Describe()
        result = describe._indices_summary([True, False, True], matched=False)
        assert result == "[1]"

    def test_indices_summary_none_matched(self):
        """Indices summary when none matched."""
        describe = Describe()
        result = describe._indices_summary([False, False, False], matched=True)
        assert result == "none"

    def test_indices_summary_all_matched(self):
        """Indices summary when all matched."""
        describe = Describe()
        result = describe._indices_summary([True, True, True], matched=False)
        assert result == "none"

    def test_indices_summary_many_items_truncated(self):
        """Indices summary truncates when more than 5 items."""
        describe = Describe()
        results = [True] * 10
        result = describe._indices_summary(results, matched=True)
        assert "+5 more" in result
        assert "[0, 1, 2, 3, 4" in result

    def test_indices_summary_exactly_five(self):
        """Indices summary shows all 5 items without truncation."""
        describe = Describe()
        results = [True] * 5
        result = describe._indices_summary(results, matched=True)
        assert result == "[0, 1, 2, 3, 4]"


class TestDescribeForAny:
    """Tests for the _describe_for_any method."""

    def test_for_any_passed(self):
        """Description when for_any passes."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False}, {"a": True}])
        result = describe._describe_for_any(mpr, passed=True)
        assert "✓" in result
        assert "At least one item matched" in result
        assert "1" in result  # index of matched item

    def test_for_any_failed(self):
        """Description when for_any fails."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False}, {"a": False}])
        result = describe._describe_for_any(mpr, passed=False)
        assert "✗" in result
        assert "none did" in result


class TestDescribeForAll:
    """Tests for the _describe_for_all method."""

    def test_for_all_passed(self):
        """Description when for_all passes."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}, {"a": True}])
        result = describe._describe_for_all(mpr, passed=True)
        assert "✓" in result
        assert "All 2 items matched" in result

    def test_for_all_failed(self):
        """Description when for_all fails."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}, {"a": False}])
        result = describe._describe_for_all(mpr, passed=False)
        assert "✗" in result
        assert "some failed" in result
        assert "1" in result  # index of failed item


class TestDescribeForNone:
    """Tests for the _describe_for_none method."""

    def test_for_none_passed(self):
        """Description when for_none passes."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False}, {"a": False}])
        result = describe._describe_for_none(mpr, passed=True)
        assert "✓" in result
        assert "No items matched" in result
        assert "as expected" in result

    def test_for_none_failed(self):
        """Description when for_none fails."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False}, {"a": True}])
        result = describe._describe_for_none(mpr, passed=False)
        assert "✗" in result
        assert "some did" in result


class TestDescribeForOne:
    """Tests for the _describe_for_one method."""

    def test_for_one_passed(self):
        """Description when for_one passes."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False}, {"a": True}, {"a": False}])
        result = describe._describe_for_one(mpr, passed=True)
        assert "✓" in result
        assert "Exactly one item matched" in result
        assert "index: 1" in result

    def test_for_one_failed_none_matched(self):
        """Description when for_one fails with no matches."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False}, {"a": False}])
        result = describe._describe_for_one(mpr, passed=False)
        assert "✗" in result
        assert "none did" in result

    def test_for_one_failed_multiple_matched(self):
        """Description when for_one fails with multiple matches."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}, {"a": True}, {"a": False}])
        result = describe._describe_for_one(mpr, passed=False)
        assert "✗" in result
        assert "2 matched" in result


class TestDescribeForN:
    """Tests for the _describe_for_n method."""

    def test_for_n_passed(self):
        """Description when for_n passes."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}, {"a": True}, {"a": False}])
        result = describe._describe_for_n(mpr, passed=True, n=2)
        assert "✓" in result
        assert "Exactly 2 items matched" in result

    def test_for_n_failed(self):
        """Description when for_n fails."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}, {"a": False}, {"a": False}])
        result = describe._describe_for_n(mpr, passed=False, n=2)
        assert "✗" in result
        assert "Expected exactly 2" in result
        assert "1 matched" in result


class TestDescribeDefault:
    """Tests for the _describe_default method."""

    def test_default_passed(self):
        """Description for custom quantifier that passes."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}])
        result = describe._describe_default(mpr, passed=True, quantifier_name="custom")
        assert "✓ Passed" in result
        assert "custom" in result

    def test_default_failed(self):
        """Description for custom quantifier that fails."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False}])
        result = describe._describe_default(mpr, passed=False, quantifier_name="custom")
        assert "✗ Failed" in result
        assert "custom" in result


class TestDescribeMethod:
    """Tests for the describe method."""

    def test_describe_with_for_any(self):
        """describe uses for_any logic."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}])
        result = describe.describe(mpr, for_any)
        assert "At least one" in result

    def test_describe_with_for_all(self):
        """describe uses for_all logic."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}])
        result = describe.describe(mpr, for_all)
        assert "All" in result

    def test_describe_with_for_none(self):
        """describe uses for_none logic."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False}])
        result = describe.describe(mpr, for_none)
        assert "No items matched" in result

    def test_describe_with_for_one(self):
        """describe uses for_one logic."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}])
        result = describe.describe(mpr, for_one)
        assert "Exactly one" in result

    def test_describe_with_custom_quantifier(self):
        """describe uses default logic for custom quantifiers."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}, {"a": True}])
        custom_quantifier = for_n(2)
        result = describe.describe(mpr, custom_quantifier)
        assert "Passed" in result or "Failed" in result

    def test_describe_evaluates_quantifier(self):
        """describe correctly evaluates the quantifier."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}, {"a": False}])
        result = describe.describe(mpr, for_all)
        assert "✗" in result  # for_all should fail

    def test_describe_empty_results(self):
        """describe handles empty results."""
        describe = Describe()
        mpr = ModelPredicateResult([])
        result = describe.describe(mpr, for_all)
        assert "All 0 items matched" in result  # vacuous truth


class TestDescribeFailures:
    """Tests for the describe_failures method."""

    def test_describe_failures_no_failures(self):
        """describe_failures returns empty list when no failures."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}, {"a": True}])
        result = describe.describe_failures(mpr)
        assert result == []

    def test_describe_failures_single_failure(self):
        """describe_failures describes a single failure."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": True}, {"a": False}])
        result = describe.describe_failures(mpr)
        assert len(result) == 1
        assert "Item 1" in result[0]
        assert "a" in result[0]

    def test_describe_failures_multiple_failures(self):
        """describe_failures describes multiple failures."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False}, {"a": True}, {"a": False}])
        result = describe.describe_failures(mpr)
        assert len(result) == 2
        assert "Item 0" in result[0]
        assert "Item 2" in result[1]

    def test_describe_failures_multiple_keys(self):
        """describe_failures lists all failed keys."""
        describe = Describe()
        mpr = ModelPredicateResult([{"a": False, "b": False, "c": True}])
        result = describe.describe_failures(mpr)
        assert len(result) == 1
        assert "a" in result[0]
        assert "b" in result[0]

    def test_describe_failures_nested_keys(self):
        """describe_failures flattens nested keys."""
        describe = Describe()
        mpr = ModelPredicateResult([{"outer": {"inner": False}}])
        result = describe.describe_failures(mpr)
        assert len(result) == 1
        assert "outer.inner" in result[0]

    def test_describe_failures_all_keys_true(self):
        """describe_failures handles item with no failed keys."""
        describe = Describe()
        # This is an edge case where result_bool is False but no keys are False
        # (shouldn't happen in practice, but testing the fallback)
        mpr = ModelPredicateResult([])
        mpr.result_bools = [False]
        mpr.result_dicts = [{"a": True}]  # All keys true but marked as failed
        result = describe.describe_failures(mpr)
        assert len(result) == 1
        assert "Item 0: failed" in result[0]


class TestIntegration:
    """Integration tests for Describe class."""

    def test_full_workflow_passing(self):
        """Full workflow with passing results."""
        describe = Describe()
        mpr = ModelPredicateResult([
            {"name": True, "value": True},
            {"name": True, "value": True},
        ])
        
        description = describe.describe(mpr, for_all)
        failures = describe.describe_failures(mpr)
        
        assert "✓" in description
        assert failures == []

    def test_full_workflow_failing(self):
        """Full workflow with failing results."""
        describe = Describe()
        mpr = ModelPredicateResult([
            {"name": True, "value": True},
            {"name": False, "value": True},
        ])
        
        description = describe.describe(mpr, for_all)
        failures = describe.describe_failures(mpr)
        
        assert "✗" in description
        assert len(failures) == 1
        assert "name" in failures[0]

    def test_complex_nested_failures(self):
        """Complex nested structure failure descriptions."""
        describe = Describe()
        mpr = ModelPredicateResult([
            {"user": {"profile": {"name": False, "active": True}}},
        ])
        
        failures = describe.describe_failures(mpr)
        
        assert len(failures) == 1
        assert "user.profile.name" in failures[0]
