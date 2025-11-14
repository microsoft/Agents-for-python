# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.testing.assertions.check_field import (
    check_field,
    _parse_assertion,
)
from microsoft_agents.testing.assertions.type_defs import FieldAssertionType


class TestParseAssertion:

    @pytest.fixture(
        params=[
            FieldAssertionType.EQUALS,
            FieldAssertionType.NOT_EQUALS,
            FieldAssertionType.GREATER_THAN,
        ]
    )
    def assertion_type_str(self, request):
        return request.param

    @pytest.fixture(params=["simple_value", {"key": "value"}, 42])
    def assertion_value(self, request):
        return request.param

    def test_parse_assertion_dict(self, assertion_value, assertion_type_str):

        assertion, assertion_type = _parse_assertion(
            {"assertion_type": assertion_type_str, "assertion": assertion_value}
        )
        assert assertion == assertion_value
        assert assertion_type == FieldAssertionType(assertion_type_str)

    def test_parse_assertion_list(self, assertion_value, assertion_type_str):
        assertion, assertion_type = _parse_assertion(
            [assertion_type_str, assertion_value]
        )
        assert assertion == assertion_value
        assert assertion_type.value == assertion_type_str

    @pytest.mark.parametrize(
        "field",
        ["value", 123, 12.34],
    )
    def test_parse_assertion_default(self, field):
        assertion, assertion_type = _parse_assertion(field)
        assert assertion == field
        assert assertion_type == FieldAssertionType.EQUALS

    @pytest.mark.parametrize(
        "field",
        [
            {"assertion_type": FieldAssertionType.IN},
            {"assertion_type": FieldAssertionType.IN, "key": "value"},
            [FieldAssertionType.RE_MATCH],
            [],
            {"assertion_type": "invalid", "assertion": "test"},
        ],
    )
    def test_parse_assertion_none(self, field):
        assertion, assertion_type = _parse_assertion(field)
        assert assertion is None
        assert assertion_type is None


class TestCheckFieldEquals:
    """Tests for EQUALS assertion type."""

    def test_equals_with_matching_strings(self):
        assert check_field("hello", "hello", FieldAssertionType.EQUALS) is True

    def test_equals_with_non_matching_strings(self):
        assert check_field("hello", "world", FieldAssertionType.EQUALS) is False

    def test_equals_with_matching_integers(self):
        assert check_field(42, 42, FieldAssertionType.EQUALS) is True

    def test_equals_with_non_matching_integers(self):
        assert check_field(42, 43, FieldAssertionType.EQUALS) is False

    def test_equals_with_none_values(self):
        assert check_field(None, None, FieldAssertionType.EQUALS) is True

    def test_equals_with_boolean_values(self):
        assert check_field(True, True, FieldAssertionType.EQUALS) is True
        assert check_field(False, False, FieldAssertionType.EQUALS) is True
        assert check_field(True, False, FieldAssertionType.EQUALS) is False


class TestCheckFieldNotEquals:
    """Tests for NOT_EQUALS assertion type."""

    def test_not_equals_with_different_strings(self):
        assert check_field("hello", "world", FieldAssertionType.NOT_EQUALS) is True

    def test_not_equals_with_matching_strings(self):
        assert check_field("hello", "hello", FieldAssertionType.NOT_EQUALS) is False

    def test_not_equals_with_different_integers(self):
        assert check_field(42, 43, FieldAssertionType.NOT_EQUALS) is True

    def test_not_equals_with_matching_integers(self):
        assert check_field(42, 42, FieldAssertionType.NOT_EQUALS) is False


class TestCheckFieldGreaterThan:
    """Tests for GREATER_THAN assertion type."""

    def test_greater_than_with_larger_value(self):
        assert check_field(10, 5, FieldAssertionType.GREATER_THAN) is True

    def test_greater_than_with_smaller_value(self):
        assert check_field(5, 10, FieldAssertionType.GREATER_THAN) is False

    def test_greater_than_with_equal_value(self):
        assert check_field(10, 10, FieldAssertionType.GREATER_THAN) is False

    def test_greater_than_with_floats(self):
        assert check_field(10.5, 10.2, FieldAssertionType.GREATER_THAN) is True
        assert check_field(10.2, 10.5, FieldAssertionType.GREATER_THAN) is False

    def test_greater_than_with_negative_numbers(self):
        assert check_field(-5, -10, FieldAssertionType.GREATER_THAN) is True
        assert check_field(-10, -5, FieldAssertionType.GREATER_THAN) is False


class TestCheckFieldLessThan:
    """Tests for LESS_THAN assertion type."""

    def test_less_than_with_smaller_value(self):
        assert check_field(5, 10, FieldAssertionType.LESS_THAN) is True

    def test_less_than_with_larger_value(self):
        assert check_field(10, 5, FieldAssertionType.LESS_THAN) is False

    def test_less_than_with_equal_value(self):
        assert check_field(10, 10, FieldAssertionType.LESS_THAN) is False

    def test_less_than_with_floats(self):
        assert check_field(10.2, 10.5, FieldAssertionType.LESS_THAN) is True
        assert check_field(10.5, 10.2, FieldAssertionType.LESS_THAN) is False


class TestCheckFieldContains:
    """Tests for CONTAINS assertion type."""

    def test_contains_substring_in_string(self):
        assert check_field("hello world", "world", FieldAssertionType.CONTAINS) is True

    def test_contains_substring_not_in_string(self):
        assert check_field("hello world", "foo", FieldAssertionType.CONTAINS) is False

    def test_contains_element_in_list(self):
        assert check_field([1, 2, 3, 4], 3, FieldAssertionType.CONTAINS) is True

    def test_contains_element_not_in_list(self):
        assert check_field([1, 2, 3, 4], 5, FieldAssertionType.CONTAINS) is False

    def test_contains_key_in_dict(self):
        assert check_field({"a": 1, "b": 2}, "a", FieldAssertionType.CONTAINS) is True

    def test_contains_key_not_in_dict(self):
        assert check_field({"a": 1, "b": 2}, "c", FieldAssertionType.CONTAINS) is False

    def test_contains_empty_string(self):
        assert check_field("hello", "", FieldAssertionType.CONTAINS) is True


class TestCheckFieldNotContains:
    """Tests for NOT_CONTAINS assertion type."""

    def test_not_contains_substring_not_in_string(self):
        assert (
            check_field("hello world", "foo", FieldAssertionType.NOT_CONTAINS) is True
        )

    def test_not_contains_substring_in_string(self):
        assert (
            check_field("hello world", "world", FieldAssertionType.NOT_CONTAINS)
            is False
        )

    def test_not_contains_element_not_in_list(self):
        assert check_field([1, 2, 3, 4], 5, FieldAssertionType.NOT_CONTAINS) is True

    def test_not_contains_element_in_list(self):
        assert check_field([1, 2, 3, 4], 3, FieldAssertionType.NOT_CONTAINS) is False


class TestCheckFieldReMatch:
    """Tests for RE_MATCH assertion type."""

    def test_re_match_simple_pattern(self):
        assert check_field("hello123", r"hello\d+", FieldAssertionType.RE_MATCH) is True

    def test_re_match_no_match(self):
        assert check_field("hello", r"\d+", FieldAssertionType.RE_MATCH) is False

    def test_re_match_email_pattern(self):
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        assert (
            check_field("test@example.com", pattern, FieldAssertionType.RE_MATCH)
            is True
        )
        assert (
            check_field("invalid-email", pattern, FieldAssertionType.RE_MATCH) is False
        )

    def test_re_match_anchored_pattern(self):
        assert (
            check_field("hello world", r"^hello", FieldAssertionType.RE_MATCH) is True
        )
        assert (
            check_field("hello world", r"^world", FieldAssertionType.RE_MATCH) is False
        )

    def test_re_match_full_string(self):
        assert check_field("abc", r"^abc$", FieldAssertionType.RE_MATCH) is True
        assert check_field("abcd", r"^abc$", FieldAssertionType.RE_MATCH) is False

    def test_re_match_case_sensitive(self):
        assert check_field("Hello", r"hello", FieldAssertionType.RE_MATCH) is False
        assert check_field("Hello", r"Hello", FieldAssertionType.RE_MATCH) is True


class TestCheckFieldEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_assertion_type(self):
        # Passing an unsupported assertion type should return False
        assert check_field("test", "test", "INVALID_TYPE") is False

    def test_none_actual_value_with_equals(self):
        assert check_field(None, "test", FieldAssertionType.EQUALS) is False
        assert check_field(None, None, FieldAssertionType.EQUALS) is True

    def test_empty_string_comparisons(self):
        assert check_field("", "", FieldAssertionType.EQUALS) is True
        assert check_field("", "test", FieldAssertionType.EQUALS) is False

    def test_empty_list_contains(self):
        assert check_field([], "item", FieldAssertionType.CONTAINS) is False

    def test_zero_comparisons(self):
        assert check_field(0, 0, FieldAssertionType.EQUALS) is True
        assert check_field(0, 1, FieldAssertionType.LESS_THAN) is True
        assert check_field(0, -1, FieldAssertionType.GREATER_THAN) is True

    def test_type_mismatch_comparisons(self):
        # Different types should work with equality checks
        assert check_field("42", 42, FieldAssertionType.EQUALS) is False
        assert check_field("42", 42, FieldAssertionType.NOT_EQUALS) is True

    def test_complex_data_structures(self):
        actual = {"nested": {"value": 123}}
        expected = {"nested": {"value": 123}}
        assert check_field(actual, expected, FieldAssertionType.EQUALS) is True

    def test_list_equality(self):
        assert check_field([1, 2, 3], [1, 2, 3], FieldAssertionType.EQUALS) is True
        assert check_field([1, 2, 3], [3, 2, 1], FieldAssertionType.EQUALS) is False


class TestCheckFieldWithRealWorldScenarios:
    """Tests simulating real-world usage scenarios."""

    def test_validate_response_status_code(self):
        assert check_field(200, 200, FieldAssertionType.EQUALS) is True
        assert check_field(404, 200, FieldAssertionType.NOT_EQUALS) is True

    def test_validate_response_contains_keyword(self):
        response = "Success: Operation completed successfully"
        assert check_field(response, "Success", FieldAssertionType.CONTAINS) is True
        assert check_field(response, "Error", FieldAssertionType.NOT_CONTAINS) is True

    def test_validate_numeric_threshold(self):
        temperature = 72.5
        assert check_field(temperature, 100, FieldAssertionType.LESS_THAN) is True
        assert check_field(temperature, 0, FieldAssertionType.GREATER_THAN) is True

    def test_validate_message_format(self):
        message_id = "msg_20250112_001"
        pattern = r"^msg_\d{8}_\d{3}$"
        assert check_field(message_id, pattern, FieldAssertionType.RE_MATCH) is True

    def test_validate_list_membership(self):
        allowed_roles = ["admin", "user", "guest"]
        assert check_field(allowed_roles, "admin", FieldAssertionType.CONTAINS) is True
        assert (
            check_field(allowed_roles, "superuser", FieldAssertionType.NOT_CONTAINS)
            is True
        )
