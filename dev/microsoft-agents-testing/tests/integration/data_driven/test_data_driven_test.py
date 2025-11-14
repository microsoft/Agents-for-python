# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import tempfile
import os
from unittest.mock import AsyncMock

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.testing.integration.data_driven import DataDrivenTest
from microsoft_agents.testing.integration.core import AgentClient, ResponseClient

class TestDataDrivenTestSleep:
    """Tests for _sleep method."""

    @pytest.mark.asyncio
    async def test_sleep_with_explicit_duration(self):
        """Test sleep with explicit duration."""
        test_flow = {"test": []}
        ddt = DataDrivenTest(test_flow)
        
        import time
        start = time.time()
        await ddt._sleep({"duration": 0.1})
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert elapsed < 0.2  # Allow some margin

    @pytest.mark.asyncio
    async def test_sleep_with_default_duration(self):
        """Test sleep uses default duration when not specified."""
        test_flow = {
            "defaults": {
                "sleep": {"duration": 0.1}
            },
            "test": []
        }
        ddt = DataDrivenTest(test_flow)
        
        import time
        start = time.time()
        await ddt._sleep({})
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert elapsed < 0.2

    @pytest.mark.asyncio
    async def test_sleep_without_duration_defaults_to_zero(self):
        """Test sleep defaults to 0 when no duration specified."""
        test_flow = {"test": []}
        ddt = DataDrivenTest(test_flow)
        
        import time
        start = time.time()
        await ddt._sleep({})
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # Should be nearly instant

    @pytest.mark.asyncio
    async def test_sleep_overrides_default_duration(self):
        """Test that explicit duration overrides default."""
        test_flow = {
            "defaults": {
                "sleep": {"duration": 5.0}
            },
            "test": []
        }
        ddt = DataDrivenTest(test_flow)
        
        import time
        start = time.time()
        await ddt._sleep({"duration": 0.1})
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert elapsed < 0.2  # Should use explicit duration, not default


class TestDataDrivenTestRun:
    """Tests for run method."""

    @pytest.mark.asyncio
    async def test_run_empty_test(self):
        """Test running an empty test."""
        test_flow = {"test": []}
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_client.pop = AsyncMock(return_value=[])
        
        await ddt.run(agent_client, response_client)
        
        agent_client.send_activity.assert_not_called()
        response_client.pop.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_single_input_step(self):
        """Test running a test with single input step."""
        test_flow = {
            "defaults": {
                "input": {"activity": {"type": "message"} }
            },
            "test": [
                {"type": "input", "activity": {"text": "Hello"}}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        await ddt.run(agent_client, response_client)
        
        agent_client.send_activity.assert_called_once()
        call_args = agent_client.send_activity.call_args[0][0]
        assert isinstance(call_args, Activity)
        assert call_args.text == "Hello"
        assert call_args.type == "message"

    @pytest.mark.asyncio
    async def test_run_input_and_assertion_passing(self):
        """Test running a test with input and passing assertion."""
        test_flow = {
            "test": [
                {"type": "input", "activity": {"type": "message", "text": "Hello"}},
                {"type": "assertion", "activity": {"type": "message"}}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_activity = Activity(type="message", text="Response")
        response_client.pop = AsyncMock(return_value=[response_activity])
        
        # Should not raise any assertion error
        await ddt.run(agent_client, response_client)
        
        agent_client.send_activity.assert_called_once()
        response_client.pop.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_input_and_assertion_failing(self):
        """Test running a test with input and failing assertion."""
        test_flow = {
            "test": [
                {"type": "input", "activity": {"type": "message", "text": "Hello"}},
                {"type": "assertion", "activity": {"type": "event"}}  # Will fail
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_activity = Activity(type="message", text="Response")
        response_client.pop = AsyncMock(return_value=[response_activity])
        
        # Should raise assertion error
        with pytest.raises(AssertionError):
            await ddt.run(agent_client, response_client)

    @pytest.mark.asyncio
    async def test_run_assertion_accumulates_responses(self):
        """Test that assertions accumulate responses from response_client."""
        test_flow = {
            "test": [
                {"type": "input", "activity": {"type": "message", "text": "Hello"}},
                {"type": "assertion", "activity": {"type": "message"}}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        # Response client returns activities
        response_activity1 = Activity(type="message", text="Response 1")
        response_activity2 = Activity(type="message", text="Response 2")
        response_client.pop = AsyncMock(return_value=[response_activity1, response_activity2])
        
        # Should not raise - both are message type
        await ddt.run(agent_client, response_client)
        
        response_client.pop.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_multiple_assertions_accumulate(self):
        """Test that multiple assertions accumulate responses."""
        test_flow = {
            "test": [
                {"type": "input", "activity": {"type": "message", "text": "First"}},
                {"type": "assertion", "activity": {"type": "message"}, "quantifier": "one"},
                {"type": "input", "activity": {"type": "message", "text": "Second"}},
                {"type": "assertion", "activity": {"type": "message"}, "quantifier": "all"}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        # First pop returns one activity, second returns two
        response_client.pop = AsyncMock(
            side_effect=[
                [Activity(type="message", text="Response 1")],
                [Activity(type="message", text="Response 2")]
            ]
        )
        
        await ddt.run(agent_client, response_client)
        
        assert agent_client.send_activity.call_count == 2
        assert response_client.pop.call_count == 2

    @pytest.mark.asyncio
    async def test_run_with_sleep_step(self):
        """Test running a test with sleep step."""
        test_flow = {
            "test": [
                {"type": "sleep", "duration": 0.1}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        import time
        start = time.time()
        await ddt.run(agent_client, response_client)
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert elapsed < 0.2

    @pytest.mark.asyncio
    async def test_run_multiple_steps(self):
        """Test running a test with multiple steps."""
        test_flow = {
            "test": [
                {"type": "input", "activity": {"type": "message", "text": "Hello"}},
                {"type": "sleep", "duration": 0.05},
                {"type": "input", "activity": {"type": "message", "text": "World"}},
                {"type": "assertion", "activity": {"type": "message"}}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_client.pop = AsyncMock(return_value=[Activity(type="message", text="Response")])
        
        import time
        start = time.time()
        await ddt.run(agent_client, response_client)
        elapsed = time.time() - start
        
        assert agent_client.send_activity.call_count == 2
        assert elapsed >= 0.05
        response_client.pop.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_step_without_type_raises_error(self):
        """Test that a step without type raises ValueError."""
        test_flow = {
            "test": [
                {"text": "Hello"}  # Missing 'type' field
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        with pytest.raises(ValueError, match="Each step must have a 'type' field"):
            await ddt.run(agent_client, response_client)

    @pytest.mark.asyncio
    async def test_run_with_assertion_quantifier_all(self):
        """Test assertion with quantifier 'all'."""
        test_flow = {
            "test": [
                {"type": "input", "activity": {"type": "message", "text": "Hello"}},
                {
                    "type": "assertion",
                    "quantifier": "all",
                    "activity": {"type": "message"}
                }
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_client.pop = AsyncMock(return_value=[
            Activity(type="message", text="Response 1"),
            Activity(type="message", text="Response 2")
        ])
        
        # Should pass - all are message type
        await ddt.run(agent_client, response_client)

    @pytest.mark.asyncio
    async def test_run_with_assertion_quantifier_one(self):
        """Test assertion with quantifier 'one'."""
        test_flow = {
            "test": [
                {"type": "input", "activity": {"type": "message", "text": "Hello"}},
                {
                    "type": "assertion",
                    "quantifier": "one",
                    "activity": {"type": "event"}
                }
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_client.pop = AsyncMock(return_value=[
            Activity(type="message", text="Response 1"),
            Activity(type="event", name="test_event"),
            Activity(type="message", text="Response 2")
        ])
        
        # Should pass - exactly one event type
        await ddt.run(agent_client, response_client)

    @pytest.mark.asyncio
    async def test_run_with_assertion_selector(self):
        """Test assertion with selector."""
        test_flow = {
            "test": [
                {"type": "input", "activity": {"type": "message", "text": "Hello"}},
                {
                    "type": "assertion",
                    "selector": {"activity": {"type": "message"}},
                    "activity": {"text": "Response"}
                }
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_client.pop = AsyncMock(return_value=[
            Activity(type="event", name="test"),
            Activity(type="message", text="Response"),
            Activity(type="typing")
        ])
        
        # Should pass - the message activity matches
        await ddt.run(agent_client, response_client)

    @pytest.mark.asyncio
    async def test_run_populate_activity_with_defaults(self):
        """Test that input activities are populated with defaults."""
        test_flow = {
            "defaults": {
                "input": {
                    "activity": {
                        "type": "message",
                        "locale": "en-US",
                        "channelId": "test-channel"
                    }
                }
            },
            "test": [
                {"type": "input", "activity": {"text": "Hello"}}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        await ddt.run(agent_client, response_client)
        
        call_args = agent_client.send_activity.call_args[0][0]
        assert call_args.text == "Hello"
        assert call_args.type == "message"
        assert call_args.locale == "en-US"
        assert call_args.channel_id == "test-channel"


class TestDataDrivenTestIntegration:
    """Integration tests for DataDrivenTest with real scenarios."""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test a complete conversation flow."""
        test_flow = {
            "description": "Complete conversation test",
            "defaults": {
                "input": {"activity": {"type": "message", "locale": "en-US"}},
                "assertion": {"quantifier": "all"},
            },
            "test": [
                {"type": "input", "activity": {"text": "Hello"}},
                {"type": "assertion", "activity": {"type": "message"}},
                {"type": "sleep", "duration": 0.05},
                {"type": "input", "activity": {"text": "How are you?"}},
                {"type": "assertion", "activity": {"type": "message"}},
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_client.pop = AsyncMock(
            side_effect=[
                [Activity(type="message", text="Hi there!")],
                [Activity(type="message", text="I'm doing well!")]
            ]
        )
        
        await ddt.run(agent_client, response_client)
        
        assert agent_client.send_activity.call_count == 2
        assert response_client.pop.call_count == 2

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="TODO")
    async def test_with_parent_file_integration(self):
        """Test with parent file providing defaults."""
        parent_content = """defaults:
  input:
    type: message
    locale: en-US
  assertion:
    quantifier: all
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(parent_content)
            parent_file = f.name
        
        try:
            test_flow = {
                "parent": parent_file,
                "test": [
                    {"type": "input", "activity": {"text": "Hello"}},
                    {"type": "assertion", "activity": {"type": "message"}}
                ]
            }
            ddt = DataDrivenTest(test_flow)
            
            agent_client = AsyncMock(spec=AgentClient)
            response_client = AsyncMock(spec=ResponseClient)
            response_client.pop = AsyncMock(return_value=[
                Activity(type="message", text="Response")
            ])
            
            await ddt.run(agent_client, response_client)
            
            call_args = agent_client.send_activity.call_args[0][0]
            assert call_args.locale == "en-US"
            assert call_args.type == "message"
        finally:
            os.unlink(parent_file)