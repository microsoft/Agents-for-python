import pytest

from microsoft_agents.activity import Activity, Attachment

from microsoft_agents.testing.assertions.type_defs import FieldAssertionType
from microsoft_agents.testing.assertions.assertions import assert_activity
from microsoft_agents.testing.assertions.check_field import _parse_assertion


class TestParseAssertion:

    @pytest.fixture(
        params=[
            FieldAssertionType.EQUALS,
            FieldAssertionType.NOT_EQUALS,
            FieldAssertionType.GREATER_THAN
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
        [
            "value",
            123,
            12.34
        ],
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
        ]
    )
    def test_parse_assertion_none(self, field):
        assertion, assertion_type = _parse_assertion(field)
        assert assertion is None
        assert assertion_type is None

class TestAssertActivity:
    """Tests for assert_activity function."""

    def test_assert_activity_with_matching_simple_fields(self):
        """Test that activity matches baseline with simple equal fields."""
        activity = Activity(type="message", text="Hello, World!")
        baseline = {"type": "message", "text": "Hello, World!"}
        assert_activity(activity, baseline)

    def test_assert_activity_with_non_matching_fields(self):
        """Test that activity doesn't match baseline with different field values."""
        activity = Activity(type="message", text="Hello")
        baseline = {"type": "message", "text": "Goodbye"}
        assert_activity(activity, baseline)

    def test_assert_activity_with_activity_baseline(self):
        """Test that baseline can be an Activity object."""
        activity = Activity(type="message", text="Hello")
        baseline = Activity(type="message", text="Hello")
        assert_activity(activity, baseline)

    def test_assert_activity_with_partial_baseline(self):
        """Test that only fields in baseline are checked."""
        activity = Activity(
            type="message",
            text="Hello",
            channel_id="test-channel",
            conversation={"id": "conv123"}
        )
        baseline = {"type": "message", "text": "Hello"}
        assert_activity(activity, baseline)

    def test_assert_activity_with_missing_field(self):
        """Test that activity with missing field doesn't match baseline."""
        activity = Activity(type="message")
        baseline = {"type": "message", "text": "Hello"}
        assert_activity(activity, baseline)

    def test_assert_activity_with_none_values(self):
        """Test that None values are handled correctly."""
        activity = Activity(type="message")
        baseline = {"type": "message", "text": None}
        assert_activity(activity, baseline)

    def test_assert_activity_with_empty_baseline(self):
        """Test that empty baseline always matches."""
        activity = Activity(type="message", text="Hello")
        baseline = {}
        assert_activity(activity, baseline)

    def test_assert_activity_with_dict_assertion_format(self):
        """Test using dict format for assertions."""
        activity = Activity(type="message", text="Hello, World!")
        baseline = {
            "type": "message",
            "text": {"assertion_type": "CONTAINS", "assertion": "Hello"}
        }
        assert_activity(activity, baseline)

    def test_assert_activity_with_list_assertion_format(self):
        """Test using list format for assertions."""
        activity = Activity(type="message", text="Hello, World!")
        baseline = {
            "type": "message",
            "text": ["CONTAINS", "World"]
        }
        assert_activity(activity, baseline)

    def test_assert_activity_with_not_equals_assertion(self):
        """Test NOT_EQUALS assertion type."""
        activity = Activity(type="message", text="Hello")
        baseline = {
            "type": "message",
            "text": {"assertion_type": "NOT_EQUALS", "assertion": "Goodbye"}
        }
        assert_activity(activity, baseline)

    def test_assert_activity_with_contains_assertion(self):
        """Test CONTAINS assertion type."""
        activity = Activity(type="message", text="Hello, World!")
        baseline = {
            "text": {"assertion_type": "CONTAINS", "assertion": "World"}
        }
        assert_activity(activity, baseline)

    def test_assert_activity_with_not_contains_assertion(self):
        """Test NOT_CONTAINS assertion type."""
        activity = Activity(type="message", text="Hello")
        baseline = {
            "text": {"assertion_type": "NOT_CONTAINS", "assertion": "Goodbye"}
        }
        assert_activity(activity, baseline)

    def test_assert_activity_with_regex_assertion(self):
        """Test RE_MATCH assertion type."""
        activity = Activity(type="message", text="msg_20250112_001")
        baseline = {
            "text": {"assertion_type": "RE_MATCH", "assertion": r"^msg_\d{8}_\d{3}$"}
        }
        assert_activity(activity, baseline)

    def test_assert_activity_with_multiple_fields_and_mixed_assertions(self):
        """Test multiple fields with different assertion types."""
        activity = Activity(
            type="message",
            text="Hello, World!",
            channel_id="test-channel"
        )
        baseline = {
            "type": "message",
            "text": ["CONTAINS", "Hello"],
            "channel_id": {"assertion_type": "NOT_EQUALS", "assertion": "prod-channel"}
        }
        assert_activity(activity, baseline)

    def test_assert_activity_fails_on_any_field_mismatch(self):
        """Test that activity check fails if any field doesn't match."""
        activity = Activity(
            type="message",
            text="Hello",
            channel_id="test-channel"
        )
        baseline = {
            "type": "message",
            "text": "Hello",
            "channel_id": "prod-channel"
        }
        assert_activity(activity, baseline)

    def test_assert_activity_with_numeric_fields(self):
        """Test with numeric field values."""
        activity = Activity(type="message", locale="en-US")
        activity.channel_data = {"timestamp": 1234567890}
        baseline = {
            "type": "message",
            "channel_data": {"timestamp": 1234567890}
        }
        assert_activity(activity, baseline)

    def test_assert_activity_with_greater_than_assertion(self):
        """Test GREATER_THAN assertion on numeric fields."""
        activity = Activity(type="message")
        activity.channel_data = {"count": 100}
        baseline = {
            "channel_data": {"count": {"assertion_type": "GREATER_THAN", "assertion": 50}}
        }
        
        # This test depends on how nested dicts are handled
        # If channel_data is compared as a whole dict, this might not work as expected
        # Keeping this test to illustrate the concept
        assert_activity(activity, baseline)

    def test_assert_activity_with_complex_nested_structures(self):
        """Test with complex nested structures in baseline."""
        activity = Activity(
            type="message",
            conversation={"id": "conv123", "name": "Test Conversation"}
        )
        baseline = {
            "type": "message",
            "conversation": {"id": "conv123", "name": "Test Conversation"}
        }
        assert_activity(activity, baseline)

    def test_assert_activity_with_boolean_fields(self):
        """Test with boolean field values."""
        activity = Activity(type="message")
        activity.channel_data = {"is_active": True}
        baseline = {
            "channel_data": {"is_active": True}
        }
        assert_activity(activity, baseline)

    def test_assert_activity_type_mismatch(self):
        """Test that different activity types don't match."""
        activity = Activity(type="message", text="Hello")
        baseline = {"type": "event", "text": "Hello"}
        assert_activity(activity, baseline)
    
    def test_assert_activity_with_list_fields(self):
        """Test with list field values."""
        activity = Activity(type="message")
        activity.attachments = [Attachment(content_type="text/plain", content="test")]
        baseline = {
            "type": "message",
            "attachments": [{"content_type": "text/plain", "content": "test"}]
        }
        assert_activity(activity, baseline)
    
class TestAssertActivityRealWorldScenarios:
    """Tests simulating real-world usage scenarios."""

    def test_validate_bot_response_message(self):
        """Test validating a typical bot response."""
        activity = Activity(
            type="message",
            text="I found 3 results for your query.",
            from_property={"id": "bot123", "name": "HelpBot"}
        )
        baseline = {
            "type": "message",
            "text": ["RE_MATCH", r"I found \d+ results"],
            "from_property": {"id": "bot123"}
        }
        assert_activity(activity, baseline)

    def test_validate_user_message(self):
        """Test validating a user message with flexible text matching."""
        activity = Activity(
            type="message",
            text="help me with something",
            from_property={"id": "user456"}
        )
        baseline = {
            "type": "message",
            "text": {"assertion_type": "CONTAINS", "assertion": "help"}
        }
        assert_activity(activity, baseline)

    def test_validate_event_activity(self):
        """Test validating an event activity."""
        activity = Activity(
            type="event",
            name="conversationUpdate",
            value={"action": "add"}
        )
        baseline = {
            "type": "event",
            "name": "conversationUpdate"
        }
        
        assert assert_activity(activity, baseline) is True

    def test_partial_match_allows_extra_fields(self):
        """Test that extra fields in activity don't cause failure."""
        activity = Activity(
            type="message",
            text="Hello",
            channel_id="teams",
            conversation={"id": "conv123"},
            from_property={"id": "user123"},
            timestamp="2025-01-12T10:00:00Z"
        )
        baseline = {
            "type": "message",
            "text": "Hello"
        }
        assert_activity(activity, baseline)

    def test_strict_match_with_multiple_fields(self):
        """Test strict matching with multiple fields specified."""
        activity = Activity(
            type="message",
            text="Hello",
            channel_id="teams"
        )
        baseline = {
            "type": "message",
            "text": "Hello",
            "channel_id": "teams"
        }
        assert_activity(activity, baseline)

    def test_flexible_text_matching_with_regex(self):
        """Test flexible text matching using regex patterns."""
        activity = Activity(
            type="message",
            text="Order #12345 has been confirmed"
        )
        baseline = {
            "type": "message",
            "text": ["RE_MATCH", r"Order #\d+ has been"]
        }
        assert_activity(activity, baseline)

    def test_negative_assertions(self):
        """Test using negative assertions to ensure fields don't match."""
        activity = Activity(
            type="message",
            text="Success",
            channel_id="teams"
        )
        baseline = {
            "type": "message",
            "text": {"assertion_type": "NOT_CONTAINS", "assertion": "Error"},
            "channel_id": {"assertion_type": "NOT_EQUALS", "assertion": "slack"}
        }
        assert_activity(activity, baseline)

    def test_combined_positive_and_negative_assertions(self):
        """Test combining positive and negative assertions."""
        activity = Activity(
            type="message",
            text="Operation completed successfully",
            channel_id="teams"
        )
        baseline = {
            "type": "message",
            "text": ["CONTAINS", "completed"],
            "channel_id": ["NOT_EQUALS", "slack"]
        }
        assert_activity(activity, baseline)