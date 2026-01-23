# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import MagicMock

from microsoft_agents.activity import Activity, InvokeResponse

from microsoft_agents.testing.agent_test.agent_client.response_collector import (
    ResponseCollector,
)


class TestResponseCollectorInit:
    """Test ResponseCollector initialization."""

    def test_init_creates_empty_activities_list(self):
        collector = ResponseCollector()
        assert collector._activities == []

    def test_init_creates_empty_invoke_responses_list(self):
        collector = ResponseCollector()
        assert collector._invoke_responses == []

    def test_init_sets_pop_index_to_zero(self):
        collector = ResponseCollector()
        assert collector._pop_index == 0


class TestResponseCollectorAdd:
    """Test ResponseCollector.add method."""

    def test_add_activity_returns_true(self):
        collector = ResponseCollector()
        activity = Activity(type="message", text="hello")
        result = collector.add(activity)
        assert result is True

    def test_add_activity_appends_to_activities_list(self):
        collector = ResponseCollector()
        activity = Activity(type="message", text="hello")
        collector.add(activity)
        assert len(collector._activities) == 1
        assert collector._activities[0] == activity

    def test_add_invoke_response_returns_true(self):
        collector = ResponseCollector()
        invoke_response = InvokeResponse(status=200)
        result = collector.add(invoke_response)
        assert result is True

    def test_add_invoke_response_appends_to_invoke_responses_list(self):
        collector = ResponseCollector()
        invoke_response = InvokeResponse(status=200)
        collector.add(invoke_response)
        assert len(collector._invoke_responses) == 1
        assert collector._invoke_responses[0] == invoke_response

    def test_add_unknown_type_returns_false(self):
        collector = ResponseCollector()
        result = collector.add("not an activity or invoke response")
        assert result is False

    def test_add_unknown_type_does_not_modify_collections(self):
        collector = ResponseCollector()
        collector.add({"type": "message"})
        assert len(collector._activities) == 0
        assert len(collector._invoke_responses) == 0

    def test_add_none_returns_false(self):
        collector = ResponseCollector()
        result = collector.add(None)
        assert result is False

    def test_add_multiple_activities(self):
        collector = ResponseCollector()
        activity1 = Activity(type="message", text="first")
        activity2 = Activity(type="message", text="second")
        activity3 = Activity(type="typing")

        collector.add(activity1)
        collector.add(activity2)
        collector.add(activity3)

        assert len(collector._activities) == 3
        assert collector._activities[0] == activity1
        assert collector._activities[1] == activity2
        assert collector._activities[2] == activity3

    def test_add_multiple_invoke_responses(self):
        collector = ResponseCollector()
        response1 = InvokeResponse(status=200)
        response2 = InvokeResponse(status=400)

        collector.add(response1)
        collector.add(response2)

        assert len(collector._invoke_responses) == 2
        assert collector._invoke_responses[0] == response1
        assert collector._invoke_responses[1] == response2

    def test_add_mixed_types(self):
        collector = ResponseCollector()
        activity = Activity(type="message", text="hello")
        invoke_response = InvokeResponse(status=200)

        collector.add(activity)
        collector.add(invoke_response)

        assert len(collector._activities) == 1
        assert len(collector._invoke_responses) == 1


class TestResponseCollectorGetActivities:
    """Test ResponseCollector.get_activities method."""

    def test_get_activities_returns_empty_list_when_no_activities(self):
        collector = ResponseCollector()
        result = collector.get_activities()
        assert result == []

    def test_get_activities_returns_all_activities(self):
        collector = ResponseCollector()
        activity1 = Activity(type="message", text="first")
        activity2 = Activity(type="message", text="second")
        collector.add(activity1)
        collector.add(activity2)

        result = collector.get_activities()

        assert len(result) == 2
        assert activity1 in result
        assert activity2 in result

    def test_get_activities_returns_copy_of_list(self):
        collector = ResponseCollector()
        activity = Activity(type="message", text="hello")
        collector.add(activity)

        result = collector.get_activities()
        result.append(Activity(type="typing"))

        assert len(collector._activities) == 1

    def test_get_activities_resets_pop_index(self):
        collector = ResponseCollector()
        activity1 = Activity(type="message", text="first")
        activity2 = Activity(type="message", text="second")
        collector.add(activity1)
        collector.add(activity2)

        collector.get_activities()

        assert collector._pop_index == 2

    def test_get_activities_can_be_called_multiple_times(self):
        collector = ResponseCollector()
        activity = Activity(type="message", text="hello")
        collector.add(activity)

        result1 = collector.get_activities()
        result2 = collector.get_activities()

        assert result1 == result2


class TestResponseCollectorGetInvokeResponses:
    """Test ResponseCollector.get_invoke_responses method."""

    def test_get_invoke_responses_returns_empty_list_when_no_responses(self):
        collector = ResponseCollector()
        result = collector.get_invoke_responses()
        assert result == []

    def test_get_invoke_responses_returns_all_responses(self):
        collector = ResponseCollector()
        response1 = InvokeResponse(status=200)
        response2 = InvokeResponse(status=400)
        collector.add(response1)
        collector.add(response2)

        result = collector.get_invoke_responses()

        assert len(result) == 2
        assert response1 in result
        assert response2 in result

    def test_get_invoke_responses_returns_copy_of_list(self):
        collector = ResponseCollector()
        response = InvokeResponse(status=200)
        collector.add(response)

        result = collector.get_invoke_responses()
        result.append(InvokeResponse(status=500))

        assert len(collector._invoke_responses) == 1

    def test_get_invoke_responses_can_be_called_multiple_times(self):
        collector = ResponseCollector()
        response = InvokeResponse(status=200)
        collector.add(response)

        result1 = collector.get_invoke_responses()
        result2 = collector.get_invoke_responses()

        assert result1 == result2


class TestResponseCollectorPop:
    """Test ResponseCollector.pop method."""

    def test_pop_returns_empty_list_when_no_activities(self):
        collector = ResponseCollector()
        result = collector.pop()
        assert result == []

    def test_pop_returns_all_activities_on_first_call(self):
        collector = ResponseCollector()
        activity1 = Activity(type="message", text="first")
        activity2 = Activity(type="message", text="second")
        collector.add(activity1)
        collector.add(activity2)

        result = collector.pop()

        assert len(result) == 2
        assert activity1 in result
        assert activity2 in result

    def test_pop_returns_empty_list_on_second_call_without_new_activities(self):
        collector = ResponseCollector()
        activity = Activity(type="message", text="hello")
        collector.add(activity)

        collector.pop()
        result = collector.pop()

        assert result == []

    def test_pop_returns_only_new_activities(self):
        collector = ResponseCollector()
        activity1 = Activity(type="message", text="first")
        collector.add(activity1)

        collector.pop()

        activity2 = Activity(type="message", text="second")
        activity3 = Activity(type="message", text="third")
        collector.add(activity2)
        collector.add(activity3)

        result = collector.pop()

        assert len(result) == 2
        assert activity2 in result
        assert activity3 in result
        assert activity1 not in result

    def test_pop_updates_pop_index(self):
        collector = ResponseCollector()
        activity = Activity(type="message", text="hello")
        collector.add(activity)

        assert collector._pop_index == 0
        collector.pop()
        assert collector._pop_index == 1

    def test_pop_multiple_times_with_new_activities_between(self):
        collector = ResponseCollector()
        
        # First batch
        activity1 = Activity(type="message", text="first")
        collector.add(activity1)
        result1 = collector.pop()
        assert len(result1) == 1
        assert activity1 in result1

        # Second batch
        activity2 = Activity(type="message", text="second")
        collector.add(activity2)
        result2 = collector.pop()
        assert len(result2) == 1
        assert activity2 in result2

        # Third batch
        activity3 = Activity(type="message", text="third")
        activity4 = Activity(type="message", text="fourth")
        collector.add(activity3)
        collector.add(activity4)
        result3 = collector.pop()
        assert len(result3) == 2
        assert activity3 in result3
        assert activity4 in result3

    def test_pop_does_not_remove_activities_from_internal_list(self):
        collector = ResponseCollector()
        activity = Activity(type="message", text="hello")
        collector.add(activity)

        collector.pop()

        assert len(collector._activities) == 1
        assert collector._activities[0] == activity


class TestResponseCollectorInteraction:
    """Test interactions between ResponseCollector methods."""

    def test_get_activities_affects_pop(self):
        collector = ResponseCollector()
        activity1 = Activity(type="message", text="first")
        activity2 = Activity(type="message", text="second")
        collector.add(activity1)
        collector.add(activity2)

        collector.get_activities()  # This resets pop_index to end

        # Pop should return empty since get_activities reset the index
        result = collector.pop()
        assert result == []

    def test_pop_does_not_affect_get_activities(self):
        collector = ResponseCollector()
        activity1 = Activity(type="message", text="first")
        activity2 = Activity(type="message", text="second")
        collector.add(activity1)
        collector.add(activity2)

        collector.pop()

        result = collector.get_activities()
        assert len(result) == 2

    def test_mixed_add_and_pop_operations(self):
        collector = ResponseCollector()
        
        # Add and pop
        activity1 = Activity(type="message", text="first")
        collector.add(activity1)
        pop1 = collector.pop()
        assert len(pop1) == 1

        # Add more and pop
        activity2 = Activity(type="typing")
        activity3 = Activity(type="message", text="third")
        collector.add(activity2)
        collector.add(activity3)
        pop2 = collector.pop()
        assert len(pop2) == 2

        # No new activities
        pop3 = collector.pop()
        assert len(pop3) == 0

        # Get all activities still works
        all_activities = collector.get_activities()
        assert len(all_activities) == 3