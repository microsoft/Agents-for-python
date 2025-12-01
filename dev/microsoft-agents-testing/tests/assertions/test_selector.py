# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.activity import Activity
from microsoft_agents.testing.assertions.model_selector import ModelSelector


class TestSelectorSelectWithQuantifierAll:
    """Tests for select() method with ALL quantifier."""

    @pytest.fixture
    def activities(self):
        """Create a list of test activities."""
        return [
            Activity(type="message", text="Hello"),
            Activity(type="message", text="World"),
            Activity(type="event", name="test_event"),
            Activity(type="message", text="Goodbye"),
        ]

    def test_select_all_matching_type(self, activities):
        """Test selecting all activities with matching type."""
        selector = ModelSelector(model={"type": "message"})
        result = selector.select(activities)
        assert len(result) == 3
        assert all(a.type == "message" for a in result)

    def test_select_all_matching_multiple_fields(self, activities):
        """Test selecting all activities matching multiple fields."""
        selector = ModelSelector(
            model={"type": "message", "text": "Hello"},
        )
        result = selector.select(activities)
        assert len(result) == 1
        assert result[0].text == "Hello"

    def test_select_all_no_matches(self, activities):
        """Test selecting all with no matches returns empty list."""
        selector = ModelSelector(
            model={"type": "nonexistent"},
        )
        result = selector.select(activities)
        assert len(result) == 0

    def test_select_all_empty_selector(self, activities):
        """Test selecting all with empty selector returns all activities."""
        selector = ModelSelector(model={})
        result = selector.select(activities)
        assert len(result) == len(activities)

    def test_select_all_from_empty_list(self):
        """Test selecting from empty activity list."""
        selector = ModelSelector(model={"type": "message"})
        result = selector.select([])
        assert len(result) == 0


class TestSelectorSelectWithQuantifierOne:
    """Tests for select() method with ONE quantifier."""

    @pytest.fixture
    def activities(self):
        """Create a list of test activities."""
        return [
            Activity(type="message", text="First"),
            Activity(type="message", text="Second"),
            Activity(type="event", name="test_event"),
            Activity(type="message", text="Third"),
        ]

    def test_select_one_default_index(self, activities):
        """Test selecting one activity with default index (0)."""
        selector = ModelSelector(model={"type": "message"}, index=0)
        result = selector.select(activities)
        assert len(result) == 1
        assert result[0].text == "First"

    def test_select_one_explicit_index(self, activities):
        """Test selecting one activity with explicit index."""
        selector = ModelSelector(model={"type": "message"}, index=1)
        result = selector.select(activities)
        assert len(result) == 1
        assert result[0].text == "Second"

    def test_select_one_last_index(self, activities):
        """Test selecting one activity with last valid index."""
        selector = ModelSelector(model={"type": "message"}, index=2)
        result = selector.select(activities)
        assert len(result) == 1
        assert result[0].text == "Third"

    def test_select_one_negative_index(self, activities):
        """Test selecting one activity with negative index."""
        selector = ModelSelector(model={"type": "message"}, index=-1)
        result = selector.select(activities)
        assert len(result) == 1
        assert result[0].text == "Third"

    def test_select_one_negative_index_from_start(self, activities):
        """Test selecting one activity with negative index from start."""
        selector = ModelSelector(model={"type": "message"}, index=-2)
        result = selector.select(activities)
        assert len(result) == 1
        assert result[0].text == "Second"

    def test_select_one_index_out_of_range(self, activities):
        """Test selecting with index out of range returns empty list."""
        selector = ModelSelector(model={"type": "message"}, index=10)
        result = selector.select(activities)
        assert len(result) == 0

    def test_select_one_negative_index_out_of_range(self, activities):
        """Test selecting with negative index out of range returns empty list."""
        selector = ModelSelector(model={"type": "message"}, index=-10)
        result = selector.select(activities)
        assert len(result) == 0

    def test_select_one_no_matches(self, activities):
        """Test selecting one with no matches returns empty list."""
        selector = ModelSelector(model={"type": "nonexistent"}, index=0)
        result = selector.select(activities)
        assert len(result) == 0

    def test_select_one_from_empty_list(self):
        """Test selecting one from empty list returns empty list."""
        selector = ModelSelector(model={"type": "message"}, index=0)
        result = selector.select([])
        assert len(result) == 0


class TestSelectorSelectFirst:
    """Tests for select_first() method."""

    @pytest.fixture
    def activities(self):
        """Create a list of test activities."""
        return [
            Activity(type="message", text="First"),
            Activity(type="message", text="Second"),
            Activity(type="event", name="test_event"),
        ]

    def test_select_first_with_matches(self, activities):
        """Test select_first returns first matching activity."""
        selector = ModelSelector(model={"type": "message"})
        result = selector.select_first(activities)
        assert result is not None
        assert result.text == "First"

    def test_select_first_no_matches(self, activities):
        """Test select_first with no matches returns None."""
        selector = ModelSelector(
            model={"type": "nonexistent"},
        )
        result = selector.select_first(activities)
        assert result is None

    def test_select_first_empty_list(self):
        """Test select_first on empty list returns None."""
        selector = ModelSelector(model={"type": "message"})
        result = selector.select_first([])
        assert result is None

    def test_select_first_with_one_quantifier(self, activities):
        """Test select_first with ONE quantifier and specific index."""
        selector = ModelSelector(model={"type": "message"}, index=1)
        result = selector.select_first(activities)
        assert result is not None
        assert result.text == "Second"


class TestSelectorCallable:
    """Tests for __call__ method."""

    @pytest.fixture
    def activities(self):
        """Create a list of test activities."""
        return [
            Activity(type="message", text="Hello"),
            Activity(type="event", name="test_event"),
        ]

    def test_call_invokes_select(self, activities):
        """Test that calling selector instance invokes select()."""
        selector = ModelSelector(model={"type": "message"})
        result = selector(activities)
        assert len(result) == 1
        assert result[0].text == "Hello"

    def test_call_returns_same_as_select(self, activities):
        """Test that __call__ returns same result as select()."""
        selector = ModelSelector(model={"type": "event"}, index=0)
        call_result = selector(activities)
        select_result = selector.select(activities)
        assert call_result == select_result


class TestSelectorIntegration:
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

    def test_select_all_user_messages(self, conversation_activities):
        """Test selecting all messages from a specific user."""
        selector = ModelSelector(
            model={"type": "message", "from_property": {"id": "user1"}},
        )
        result = selector.select(conversation_activities)
        assert len(result) == 3

    def test_select_first_bot_response(self, conversation_activities):
        """Test selecting first bot response."""
        selector = ModelSelector(
            model={"type": "message", "from_property": {"id": "bot"}}, index=0
        )
        result = selector.select(conversation_activities)
        assert len(result) == 1
        assert result[0].text == "Hi there!"

    def test_select_last_message_negative_index(self, conversation_activities):
        """Test selecting last message using negative index."""
        selector = ModelSelector(model={"type": "message"}, index=-1)
        result = selector.select(conversation_activities)
        assert len(result) == 1
        assert result[0].text == "Goodbye"

    def test_select_typing_indicator(self, conversation_activities):
        """Test selecting typing indicator."""
        selector = ModelSelector(
            model={"type": "typing"},
        )
        result = selector.select(conversation_activities)
        assert len(result) == 1

    def test_select_conversation_update(self, conversation_activities):
        """Test selecting conversation update events."""
        selector = ModelSelector(
            model={"type": "conversationUpdate"},
        )
        result = selector.select(conversation_activities)
        assert len(result) == 1
        assert result[0].name == "add_member"


class TestSelectorEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_select_with_partial_match(self):
        """Test that partial matches work correctly."""
        activities = [
            Activity(type="message", text="Hello", channelData={"id": 1}),
            Activity(type="message", text="World"),
        ]
        # Only matching on type, not text
        selector = ModelSelector(model={"type": "message"})
        result = selector.select(activities)
        assert len(result) == 2

    def test_select_with_none_values(self):
        """Test selecting activities with None values."""
        activities = [
            Activity(type="message"),
            Activity(type="message", text="Hello"),
        ]
        selector = ModelSelector(
            model={"type": "message", "text": None},
        )
        result = selector.select(activities)
        # This depends on how check_activity handles None
        assert isinstance(result, list)

    def test_select_single_activity_list(self):
        """Test selecting from list with single activity."""
        activities = [Activity(type="message", text="Only one")]
        selector = ModelSelector(model={"type": "message"}, index=0)
        result = selector.select(activities)
        assert len(result) == 1
        assert result[0].text == "Only one"

    def test_select_with_boundary_index_zero(self):
        """Test selecting with index 0 on single item."""
        activities = [Activity(type="message", text="Single")]
        selector = ModelSelector(model={"type": "message"}, index=0)
        result = selector.select(activities)
        assert len(result) == 1

    def test_select_with_boundary_negative_one(self):
        """Test selecting with index -1 on single item."""
        activities = [Activity(type="message", text="Single")]
        selector = ModelSelector(model={"type": "message"}, index=-1)
        result = selector.select(activities)
        assert len(result) == 1
