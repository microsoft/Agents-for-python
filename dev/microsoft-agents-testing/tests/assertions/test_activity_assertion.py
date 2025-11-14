# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import Activity
from microsoft_agents.testing import (
    ActivityAssertion,
    Selector,
    AssertionQuantifier,
    FieldAssertionType,
)


class TestActivityAssertionCheckWithQuantifierAll:
    """Tests for check() method with ALL quantifier."""

    @pytest.fixture
    def activities(self):
        """Create a list of test activities."""
        return [
            Activity(type="message", text="Hello"),
            Activity(type="message", text="World"),
            Activity(type="event", name="test_event"),
            Activity(type="message", text="Goodbye"),
        ]

    def test_check_all_matching_activities(self, activities):
        """Test that all matching activities pass the assertion."""
        assertion = ActivityAssertion(
            assertion={"type": "message"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(activities)
        assert passes is True
        assert error is None

    def test_check_all_with_one_failing_activity(self, activities):
        """Test that one failing activity causes ALL assertion to fail."""
        assertion = ActivityAssertion(
            assertion={"text": "Hello"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(activities)
        assert passes is False
        assert error is not None
        assert "Activity did not match the assertion" in error

    def test_check_all_with_empty_selector(self, activities):
        """Test ALL quantifier with empty selector (matches all activities)."""
        assertion = ActivityAssertion(
            assertion={"type": "message"},
            selector=Selector(selector={}),
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(activities)
        # Should fail because not all activities are messages
        assert passes is False

    def test_check_all_with_empty_activities(self):
        """Test ALL quantifier with empty activities list."""
        assertion = ActivityAssertion(
            assertion={"type": "message"}, quantifier=AssertionQuantifier.ALL
        )
        passes, error = assertion.check([])
        assert passes is True
        assert error is None

    def test_check_all_with_complex_assertion(self, activities):
        """Test ALL quantifier with complex nested assertion."""
        complex_activities = [
            Activity(type="message", text="Hello", channelData={"id": 1}),
            Activity(type="message", text="World", channelData={"id": 2}),
        ]
        assertion = ActivityAssertion(
            assertion={"type": "message"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(complex_activities)
        assert passes is True


class TestActivityAssertionCheckWithQuantifierNone:
    """Tests for check() method with NONE quantifier."""

    @pytest.fixture
    def activities(self):
        """Create a list of test activities."""
        return [
            Activity(type="message", text="Hello"),
            Activity(type="message", text="World"),
            Activity(type="event", name="test_event"),
        ]

    def test_check_none_with_no_matches(self, activities):
        """Test NONE quantifier when no activities match."""
        assertion = ActivityAssertion(
            assertion={"text": "Nonexistent"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.NONE,
        )
        passes, error = assertion.check(activities)
        assert passes is True
        assert error is None

    def test_check_none_with_one_match(self, activities):
        """Test NONE quantifier fails when one activity matches."""
        assertion = ActivityAssertion(
            assertion={"text": "Hello"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.NONE,
        )
        passes, error = assertion.check(activities)
        assert passes is False
        assert error is not None
        assert "Activity matched the assertion when none were expected" in error

    def test_check_none_with_all_matching(self, activities):
        """Test NONE quantifier fails when all activities match."""
        assertion = ActivityAssertion(
            assertion={"type": "message"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.NONE,
        )
        passes, error = assertion.check(activities)
        assert passes is False

    def test_check_none_with_empty_activities(self):
        """Test NONE quantifier with empty activities list."""
        assertion = ActivityAssertion(
            assertion={"type": "message"}, quantifier=AssertionQuantifier.NONE
        )
        passes, error = assertion.check([])
        assert passes is True
        assert error is None


class TestActivityAssertionCheckWithQuantifierOne:
    """Tests for check() method with ONE quantifier."""

    @pytest.fixture
    def activities(self):
        """Create a list of test activities."""
        return [
            Activity(type="message", text="First"),
            Activity(type="message", text="Second"),
            Activity(type="event", name="test_event"),
            Activity(type="message", text="Third"),
        ]

    def test_check_one_with_exactly_one_match(self, activities):
        """Test ONE quantifier passes when exactly one activity matches."""
        assertion = ActivityAssertion(
            assertion={"text": "First"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.ONE,
        )
        passes, error = assertion.check(activities)
        assert passes is True
        assert error is None

    def test_check_one_with_no_matches(self, activities):
        """Test ONE quantifier fails when no activities match."""
        assertion = ActivityAssertion(
            assertion={"text": "Nonexistent"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.ONE,
        )
        passes, error = assertion.check(activities)
        assert passes is False
        assert error is not None
        assert "Expected exactly one activity" in error
        assert "found 0" in error

    def test_check_one_with_multiple_matches(self, activities):
        """Test ONE quantifier fails when multiple activities match."""
        assertion = ActivityAssertion(
            assertion={"type": "message"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.ONE,
        )
        passes, error = assertion.check(activities)
        assert passes is False
        assert error is not None
        assert "Expected exactly one activity" in error
        assert "found 3" in error

    def test_check_one_with_empty_activities(self):
        """Test ONE quantifier with empty activities list."""
        assertion = ActivityAssertion(
            assertion={"type": "message"}, quantifier=AssertionQuantifier.ONE
        )
        passes, error = assertion.check([])
        assert passes is False
        assert "found 0" in error


class TestActivityAssertionCheckWithQuantifierAny:
    """Tests for check() method with ANY quantifier."""

    @pytest.fixture
    def activities(self):
        """Create a list of test activities."""
        return [
            Activity(type="message", text="Hello"),
            Activity(type="message", text="World"),
            Activity(type="event", name="test_event"),
        ]

    def test_check_any_basic_functionality(self, activities):
        """Test that ANY quantifier exists and can be used."""
        # ANY quantifier doesn't have special logic in the current implementation
        # but should not cause errors
        assertion = ActivityAssertion(
            assertion={"type": "message"}, quantifier=AssertionQuantifier.ANY
        )
        passes, error = assertion.check(activities)
        # Based on the implementation, ANY behaves like checking if count > 0
        assert passes is True
        assert error is None


class TestActivityAssertionCallable:
    """Tests for __call__ method."""

    @pytest.fixture
    def activities(self):
        """Create a list of test activities."""
        return [
            Activity(type="message", text="Hello"),
            Activity(type="event", name="test_event"),
        ]

    def test_call_invokes_check(self, activities):
        """Test that calling assertion instance invokes check()."""
        assertion = ActivityAssertion(
            assertion={"type": "message"}, quantifier=AssertionQuantifier.ALL
        )
        result = assertion(activities)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)

    def test_call_returns_same_as_check(self, activities):
        """Test that __call__ returns same result as check()."""
        assertion = ActivityAssertion(
            assertion={"type": "message"},
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.ALL,
        )
        call_result = assertion(activities)
        check_result = assertion.check(activities)
        assert call_result == check_result


class TestActivityAssertionFromConfig:
    """Tests for from_config static method."""

    def test_from_config_minimal(self):
        """Test creating assertion from minimal config."""
        config = {}
        assertion = ActivityAssertion.from_config(config)
        assert assertion._assertion == {}
        assert assertion._quantifier == AssertionQuantifier.ALL

    def test_from_config_with_assertion(self):
        """Test creating assertion from config with assertion field."""
        config = {"assertion": {"type": "message", "text": "Hello"}}
        assertion = ActivityAssertion.from_config(config)
        assert assertion._assertion == config["assertion"]

    def test_from_config_with_selector(self):
        """Test creating assertion from config with selector field."""
        config = {"selector": {"selector": {"type": "message"}, "quantifier": "ALL"}}
        assertion = ActivityAssertion.from_config(config)
        assert assertion._selector is not None

    def test_from_config_with_quantifier(self):
        """Test creating assertion from config with quantifier field."""
        config = {"quantifier": "one"}
        assertion = ActivityAssertion.from_config(config)
        assert assertion._quantifier == AssertionQuantifier.ONE

    def test_from_config_with_all_fields(self):
        """Test creating assertion from config with all fields."""
        config = {
            "assertion": {"type": "message"},
            "selector": {
                "selector": {"text": "Hello"},
                "quantifier": "ONE",
                "index": 0,
            },
            "quantifier": "all",
        }
        assertion = ActivityAssertion.from_config(config)
        assert assertion._assertion == {"type": "message"}
        assert assertion._quantifier == AssertionQuantifier.ALL

    def test_from_config_with_case_insensitive_quantifier(self):
        """Test from_config handles case-insensitive quantifier strings."""
        for quantifier_str in ["all", "ALL", "All", "ONE", "one", "NONE", "none"]:
            config = {"quantifier": quantifier_str}
            assertion = ActivityAssertion.from_config(config)
            assert isinstance(assertion._quantifier, AssertionQuantifier)

    def test_from_config_with_complex_assertion(self):
        """Test creating assertion from config with complex nested assertion."""
        config = {
            "assertion": {"type": "message", "channelData": {"nested": {"value": 123}}},
            "quantifier": "all",
        }
        assertion = ActivityAssertion.from_config(config)
        assert assertion._assertion["type"] == "message"
        assert assertion._assertion["channelData"]["nested"]["value"] == 123


class TestActivityAssertionCombineErrors:
    """Tests for _combine_assertion_errors static method."""

    def test_combine_empty_errors(self):
        """Test combining empty error list."""
        result = ActivityAssertion._combine_assertion_errors([])
        assert result == ""

    def test_combine_single_error(self):
        """Test combining single error."""
        from microsoft_agents.testing.assertions.type_defs import (
            AssertionErrorData,
            FieldAssertionType,
        )

        error = AssertionErrorData(
            field_path="activity.text",
            actual_value="Hello",
            assertion="World",
            assertion_type=FieldAssertionType.EQUALS,
        )
        result = ActivityAssertion._combine_assertion_errors([error])
        assert "activity.text" in result
        assert "Hello" in result

    def test_combine_multiple_errors(self):
        """Test combining multiple errors."""
        from microsoft_agents.testing.assertions.type_defs import (
            AssertionErrorData,
            FieldAssertionType,
        )

        errors = [
            AssertionErrorData(
                field_path="activity.text",
                actual_value="Hello",
                assertion="World",
                assertion_type=FieldAssertionType.EQUALS,
            ),
            AssertionErrorData(
                field_path="activity.type",
                actual_value="message",
                assertion="event",
                assertion_type=FieldAssertionType.EQUALS,
            ),
        ]
        result = ActivityAssertion._combine_assertion_errors(errors)
        assert "activity.text" in result
        assert "activity.type" in result
        assert "\n" in result


class TestActivityAssertionIntegration:
    """Integration tests with realistic scenarios."""

    @pytest.fixture
    def conversation_activities(self):
        """Create a realistic conversation flow."""
        return [
            Activity(type="conversationUpdate", name="add_member"),
            Activity(type="message", text="Hello bot", from_property={"id": "user1"}),
            Activity(type="message", text="Hi there!", from_property={"id": "bot"}),
            Activity(
                type="message", text="How are you?", from_property={"id": "user1"}
            ),
            Activity(
                type="message", text="I'm doing well!", from_property={"id": "bot"}
            ),
            Activity(type="typing"),
            Activity(type="message", text="Goodbye", from_property={"id": "user1"}),
        ]

    def test_assert_all_user_messages_have_from_property(self, conversation_activities):
        """Test that all user messages have a from_property."""
        assertion = ActivityAssertion(
            assertion={"from_property": {"id": "user1"}},
            selector=Selector(
                selector={"type": "message", "from_property": {"id": "user1"}},
            ),
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(conversation_activities)
        assert passes is True

    def test_assert_no_error_messages(self, conversation_activities):
        """Test that there are no error messages in the conversation."""
        assertion = ActivityAssertion(
            assertion={"type": "error"},
            selector=Selector(selector={}),
            quantifier=AssertionQuantifier.NONE,
        )
        passes, error = assertion.check(conversation_activities)
        assert passes is True

    def test_assert_exactly_one_conversation_update(self, conversation_activities):
        """Test that there's exactly one conversation update."""
        assertion = ActivityAssertion(
            assertion={"type": "conversationUpdate"},
            selector=Selector(selector={"type": "conversationUpdate"}),
            quantifier=AssertionQuantifier.ONE,
        )
        passes, error = assertion.check(conversation_activities)
        assert passes is True

    def test_assert_first_message_is_greeting(self, conversation_activities):
        """Test that the first message contains a greeting."""
        assertion = ActivityAssertion(
            assertion={"text": {"assertion_type": "CONTAINS", "assertion": "Hello"}},
            selector=Selector(selector={"type": "message"}, index=0),
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(conversation_activities)
        assert passes is True

    def test_complex_multi_field_assertion(self, conversation_activities):
        """Test complex assertion with multiple fields."""
        assertion = ActivityAssertion(
            assertion={"type": "message", "from_property": {"id": "bot"}},
            selector=Selector(
                selector={"type": "message", "from_property": {"id": "bot"}},
            ),
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(conversation_activities)
        assert passes is True


class TestActivityAssertionEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_assertion_matches_all(self):
        """Test that empty assertion matches all activities."""
        activities = [
            Activity(type="message", text="Hello"),
            Activity(type="event", name="test"),
        ]
        assertion = ActivityAssertion(assertion={}, quantifier=AssertionQuantifier.ALL)
        passes, error = assertion.check(activities)
        assert passes is True

    def test_assertion_with_none_values(self):
        """Test assertion with None values."""
        activities = [Activity(type="message")]
        assertion = ActivityAssertion(
            assertion={"text": None}, quantifier=AssertionQuantifier.ALL
        )
        passes, error = assertion.check(activities)
        # This behavior depends on check_activity implementation
        assert isinstance(passes, bool)

    def test_selector_filters_before_assertion(self):
        """Test that selector filters activities before assertion check."""
        activities = [
            Activity(type="message", text="Hello"),
            Activity(type="event", name="test"),
            Activity(type="message", text="World"),
        ]
        # Selector gets only messages, assertion checks for specific text
        assertion = ActivityAssertion(
            assertion={"text": "Hello"},
            selector=Selector(selector={"type": "message"}, index=0),
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(activities)
        assert passes is True

    def test_assertion_error_message_format(self):
        """Test that error messages are properly formatted."""
        activities = [Activity(type="message", text="Wrong")]
        assertion = ActivityAssertion(
            assertion={"text": "Expected"}, quantifier=AssertionQuantifier.ALL
        )
        passes, error = assertion.check(activities)
        assert passes is False
        assert error is not None
        assert "Activity did not match the assertion" in error
        assert "Error:" in error

    def test_multiple_activities_same_content(self):
        """Test handling multiple activities with identical content."""
        activities = [
            Activity(type="message", text="Hello"),
            Activity(type="message", text="Hello"),
            Activity(type="message", text="Hello"),
        ]
        assertion = ActivityAssertion(
            assertion={"text": "Hello"}, quantifier=AssertionQuantifier.ALL
        )
        passes, error = assertion.check(activities)
        assert passes is True

    def test_assertion_with_unset_fields(self):
        """Test assertion against activities with unset fields."""
        activities = [
            Activity(type="message"),  # No text field set
        ]
        assertion = ActivityAssertion(
            assertion={"type": "message"}, quantifier=AssertionQuantifier.ALL
        )
        passes, error = assertion.check(activities)
        assert passes is True


class TestActivityAssertionErrorMessages:
    """Tests specifically for error message content and formatting."""

    def test_all_quantifier_error_includes_activity(self):
        """Test that ALL quantifier error includes the failing activity."""
        activities = [Activity(type="message", text="Wrong")]
        assertion = ActivityAssertion(
            assertion={"text": "Expected"}, quantifier=AssertionQuantifier.ALL
        )
        passes, error = assertion.check(activities)
        assert passes is False
        assert "Activity did not match the assertion" in error

    def test_none_quantifier_error_includes_activity(self):
        """Test that NONE quantifier error includes the matching activity."""
        activities = [Activity(type="message", text="Unexpected")]
        assertion = ActivityAssertion(
            assertion={"text": "Unexpected"}, quantifier=AssertionQuantifier.NONE
        )
        passes, error = assertion.check(activities)
        assert passes is False
        assert "Activity matched the assertion when none were expected" in error

    def test_one_quantifier_error_includes_count(self):
        """Test that ONE quantifier error includes the actual count."""
        activities = [
            Activity(type="message"),
            Activity(type="message"),
        ]
        assertion = ActivityAssertion(
            assertion={"type": "message"}, quantifier=AssertionQuantifier.ONE
        )
        passes, error = assertion.check(activities)
        assert passes is False
        assert "Expected exactly one activity" in error
        assert "2" in error


class TestActivityAssertionRealWorldScenarios:
    """Tests simulating real-world bot testing scenarios."""

    def test_validate_welcome_message_sent(self):
        """Test that a welcome message is sent when user joins."""
        activities = [
            Activity(type="conversationUpdate", name="add_member"),
            Activity(type="message", text="Welcome to our bot!"),
        ]
        assertion = ActivityAssertion(
            assertion={
                "type": "message",
                "text": {"assertion_type": "CONTAINS", "assertion": "Welcome"},
            },
            selector=Selector(selector={"type": "message"}),
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(activities)
        assert passes is True

    def test_validate_no_duplicate_responses(self):
        """Test that bot doesn't send duplicate responses."""
        activities = [
            Activity(type="message", text="Response 1"),
            Activity(type="message", text="Response 2"),
            Activity(type="message", text="Response 3"),
        ]
        # Check that exactly one of each unique response exists
        for response_text in ["Response 1", "Response 2", "Response 3"]:
            assertion = ActivityAssertion(
                assertion={"text": response_text},
                selector=Selector(selector={"type": "message"}),
                quantifier=AssertionQuantifier.ONE,
            )
            passes, error = assertion.check(activities)
            assert passes is True

    def test_validate_error_handling_response(self):
        """Test that bot responds appropriately to errors."""
        activities = [
            Activity(type="message", text="invalid command"),
            Activity(type="message", text="I'm sorry, I didn't understand that."),
        ]
        assertion = ActivityAssertion(
            assertion={
                "text": {
                    "assertion_type": "RE_MATCH",
                    "assertion": "sorry|understand|help",
                }
            },
            selector=Selector(selector={"type": "message"}, index=-1),  # Last message
            quantifier=AssertionQuantifier.ALL,
        )
        passes, error = assertion.check(activities)
        assert not passes
        assert "sorry" in error and "understand" in error and "help" in error
        assert FieldAssertionType.RE_MATCH.name in error

    def test_validate_typing_indicator_before_response(self):
        """Test that typing indicator is sent before response."""
        activities = [
            Activity(type="message", text="User question"),
            Activity(type="typing"),
            Activity(type="message", text="Bot response"),
        ]
        # Verify typing indicator exists
        typing_assertion = ActivityAssertion(
            assertion={"type": "typing"},
            selector=Selector(selector={"type": "typing"}),
            quantifier=AssertionQuantifier.ONE,
        )
        passes, error = typing_assertion.check(activities)
        assert passes is True

    def test_validate_conversation_flow_order(self):
        """Test that conversation follows expected flow."""
        activities = [
            Activity(type="conversationUpdate"),
            Activity(type="message", text="User: Hello"),
            Activity(type="typing"),
            Activity(type="message", text="Bot: Hi!"),
        ]

        # Test each step individually
        steps = [
            ({"type": "conversationUpdate"}, 0),
            ({"type": "message"}, 1),
            ({"type": "typing"}, 2),
            ({"type": "message"}, 3),
        ]

        for assertion_dict, expected_index in steps:
            assertion = ActivityAssertion(
                assertion=assertion_dict,
                selector=Selector(selector={}, index=expected_index),
                quantifier=AssertionQuantifier.ALL,
            )
            passes, error = assertion.check(activities)
            assert passes is True, f"Failed at index {expected_index}: {error}"
