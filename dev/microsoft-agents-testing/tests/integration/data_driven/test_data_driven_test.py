# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.testing.integration.data_driven import DataDrivenTest
from microsoft_agents.testing.integration.core import AgentClient, ResponseClient


class TestDataDrivenTestInit:
    """Tests for DataDrivenTest initialization."""

    def test_init_minimal_config(self):
        """Test initialization with minimal configuration."""
        test_flow = {"test": []}
        ddt = DataDrivenTest(test_flow)
        
        assert ddt._description == ""
        assert ddt._input_defaults == {}
        assert ddt._assertion_defaults == {}
        assert ddt._sleep_defaults == {}
        assert ddt._test == []

    def test_init_with_description(self):
        """Test initialization with description."""
        test_flow = {
            "description": "Test description",
            "test": []
        }
        ddt = DataDrivenTest(test_flow)
        
        assert ddt._description == "Test description"

    def test_init_with_defaults(self):
        """Test initialization with defaults."""
        test_flow = {
            "defaults": {
                "input": {"type": "message", "text": "default text"},
                "assertion": {"type": "message"},
                "sleep": {"duration": 1.5}
            },
            "test": []
        }
        ddt = DataDrivenTest(test_flow)
        
        assert ddt._input_defaults == {"type": "message", "text": "default text"}
        assert ddt._assertion_defaults == {"type": "message"}
        assert ddt._sleep_defaults == {"duration": 1.5}

    def test_init_with_parent(self):
        """Test initialization with parent file."""
        parent_content = """
defaults:
  input:
    type: message
    locale: en-US
  assertion:
    type: message
  sleep:
    duration: 2.0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(parent_content)
            parent_file = f.name
        
        try:
            test_flow = {
                "parent": parent_file,
                "defaults": {
                    "input": {"text": "child text"},
                    "assertion": {"text": "child assertion"}
                },
                "test": []
            }
            ddt = DataDrivenTest(test_flow)
            
            # Parent defaults should be merged with child defaults
            assert ddt._input_defaults["type"] == "message"
            assert ddt._input_defaults["locale"] == "en-US"
            assert ddt._input_defaults["text"] == "child text"
            assert ddt._assertion_defaults["type"] == "message"
            assert ddt._assertion_defaults["text"] == "child assertion"
            assert ddt._sleep_defaults["duration"] == 2.0
        finally:
            os.unlink(parent_file)

    def test_init_with_test_steps(self):
        """Test initialization with test steps."""
        test_flow = {
            "test": [
                {"type": "input", "text": "Hello"},
                {"type": "assertion", "text": "Response"},
                {"type": "sleep", "duration": 1.0}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        assert len(ddt._test) == 3
        assert ddt._test[0]["type"] == "input"
        assert ddt._test[1]["type"] == "assertion"
        assert ddt._test[2]["type"] == "sleep"


class TestDataDrivenTestLoadInput:
    """Tests for _load_input method."""

    def test_load_input_minimal(self):
        """Test loading input with minimal data."""
        test_flow = {"test": []}
        ddt = DataDrivenTest(test_flow)
        
        input_data = {"type": "message", "text": "Hello"}
        activity = ddt._load_input(input_data)
        
        assert isinstance(activity, Activity)
        assert activity.type == "message"
        assert activity.text == "Hello"

    def test_load_input_with_defaults(self):
        """Test loading input merges with defaults."""
        test_flow = {
            "defaults": {
                "input": {
                    "type": "message",
                    "locale": "en-US",
                    "text": "default text"
                }
            },
            "test": []
        }
        ddt = DataDrivenTest(test_flow)
        
        input_data = {"text": "Hello"}
        activity = ddt._load_input(input_data)
        
        assert activity.type == "message"
        assert activity.text == "Hello"
        assert activity.locale == "en-US"

    def test_load_input_overrides_defaults(self):
        """Test that input data overrides defaults."""
        test_flow = {
            "defaults": {
                "input": {"type": "message", "text": "default"}
            },
            "test": []
        }
        ddt = DataDrivenTest(test_flow)
        
        input_data = {"type": "event", "text": "override"}
        activity = ddt._load_input(input_data)
        
        assert activity.type == "event"
        assert activity.text == "override"


class TestDataDrivenTestLoadAssertion:
    """Tests for _load_assertion method."""

    def test_load_assertion_minimal(self):
        """Test loading assertion with minimal data."""
        test_flow = {"test": []}
        ddt = DataDrivenTest(test_flow)
        
        assertion_data = {"type": "message"}
        result = ddt._load_assertion(assertion_data)
        
        assert result == {"type": "message"}

    def test_load_assertion_with_defaults(self):
        """Test loading assertion merges with defaults."""
        test_flow = {
            "defaults": {
                "assertion": {
                    "type": "message",
                    "quantifier": "all"
                }
            },
            "test": []
        }
        ddt = DataDrivenTest(test_flow)
        
        assertion_data = {"text": "Hello"}
        result = ddt._load_assertion(assertion_data)
        
        assert result["type"] == "message"
        assert result["quantifier"] == "all"
        assert result["text"] == "Hello"

    def test_load_assertion_overrides_defaults(self):
        """Test that assertion data overrides defaults."""
        test_flow = {
            "defaults": {
                "assertion": {"type": "message", "quantifier": "all"}
            },
            "test": []
        }
        ddt = DataDrivenTest(test_flow)
        
        assertion_data = {"type": "event", "quantifier": "one"}
        result = ddt._load_assertion(assertion_data)
        
        assert result["type"] == "event"
        assert result["quantifier"] == "one"


class TestDataDrivenTestSleep:
    """Tests for _sleep method."""

    @pytest.mark.asyncio
    async def test_sleep_with_explicit_duration(self):
        """Test sleep with explicit duration."""
        test_flow = {"test": []}
        ddt = DataDrivenTest(test_flow)
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await ddt._sleep({"duration": 2.5})
            mock_sleep.assert_called_once_with(2.5)

    @pytest.mark.asyncio
    async def test_sleep_with_default_duration(self):
        """Test sleep uses default duration when not specified."""
        test_flow = {
            "defaults": {
                "sleep": {"duration": 3.0}
            },
            "test": []
        }
        ddt = DataDrivenTest(test_flow)
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await ddt._sleep({})
            mock_sleep.assert_called_once_with(3.0)

    @pytest.mark.asyncio
    async def test_sleep_without_duration_defaults_to_zero(self):
        """Test sleep defaults to 0 when no duration specified."""
        test_flow = {"test": []}
        ddt = DataDrivenTest(test_flow)
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await ddt._sleep({})
            mock_sleep.assert_called_once_with(0)


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
                "input": {"type": "message"}
            },
            "test": [
                {"type": "input", "text": "Hello"}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        with patch('microsoft_agents.testing.utils.populate_activity') as mock_populate:
            mock_populate.side_effect = lambda act, defaults: act
            await ddt.run(agent_client, response_client)
        
        agent_client.send_activity.assert_called_once()
        call_args = agent_client.send_activity.call_args[0][0]
        assert isinstance(call_args, Activity)
        assert call_args.text == "Hello"

    @pytest.mark.asyncio
    async def test_run_input_and_assertion(self):
        """Test running a test with input and assertion steps."""
        test_flow = {
            "test": [
                {"type": "input", "type": "message", "text": "Hello"},
                {"type": "assertion", "assertion": {"type": "message"}}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_activity = Activity(type="message", text="Response")
        response_client.pop = AsyncMock(return_value=[response_activity])
        
        mock_assertion = MagicMock(return_value=(True, None))
        
        with patch('microsoft_agents.testing.utils.populate_activity') as mock_populate:
            mock_populate.side_effect = lambda act, defaults: act
            with patch('microsoft_agents.testing.assertions.ActivityAssertion.from_config', return_value=mock_assertion):
                await ddt.run(agent_client, response_client)
        
        agent_client.send_activity.assert_called_once()
        response_client.pop.assert_called_once()
        mock_assertion.assert_called_once_with([response_activity])

    @pytest.mark.asyncio
    async def test_run_assertion_accumulates_responses(self):
        """Test that assertions accumulate responses from previous steps."""
        test_flow = {
            "test": [
                {"type": "input", "type": "message", "text": "Hello"},
                {"type": "assertion", "assertion": {"type": "message"}}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        # Response client returns activities on first call, empty on second
        response_activity1 = Activity(type="message", text="Response 1")
        response_activity2 = Activity(type="message", text="Response 2")
        response_client.pop = AsyncMock(return_value=[response_activity1, response_activity2])
        
        mock_assertion = MagicMock(return_value=(True, None))
        
        with patch('microsoft_agents.testing.utils.populate_activity') as mock_populate:
            mock_populate.side_effect = lambda act, defaults: act
            with patch('microsoft_agents.testing.assertions.ActivityAssertion.from_config', return_value=mock_assertion):
                await ddt.run(agent_client, response_client)
        
        # Check that assertion was called with accumulated responses
        mock_assertion.assert_called_once()
        call_args = mock_assertion.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0].text == "Response 1"
        assert call_args[1].text == "Response 2"

    @pytest.mark.asyncio
    async def test_run_with_sleep_step(self):
        """Test running a test with sleep step."""
        test_flow = {
            "test": [
                {"type": "sleep", "duration": 1.5}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await ddt.run(agent_client, response_client)
            mock_sleep.assert_called_once_with(1.5)

    @pytest.mark.asyncio
    async def test_run_multiple_steps(self):
        """Test running a test with multiple steps."""
        test_flow = {
            "test": [
                {"type": "input", "type": "message", "text": "Hello"},
                {"type": "sleep", "duration": 0.5},
                {"type": "input", "type": "message", "text": "World"},
                {"type": "assertion", "assertion": {"type": "message"}}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_client.pop = AsyncMock(return_value=[Activity(type="message", text="Response")])
        
        mock_assertion = MagicMock(return_value=(True, None))
        
        with patch('microsoft_agents.testing.utils.populate_activity') as mock_populate:
            mock_populate.side_effect = lambda act, defaults: act
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                with patch('microsoft_agents.testing.assertions.ActivityAssertion.from_config', return_value=mock_assertion):
                    await ddt.run(agent_client, response_client)
        
        assert agent_client.send_activity.call_count == 2
        mock_sleep.assert_called_once_with(0.5)
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
    async def test_run_uses_update_with_defaults_for_assertions(self):
        """Test that run uses update_with_defaults for assertion configuration."""
        test_flow = {
            "defaults": {
                "assertion": {"quantifier": "all"}
            },
            "test": [
                {"type": "input", "type": "message", "text": "Hello"},
                {"type": "assertion", "assertion": {"type": "message"}}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_client.pop = AsyncMock(return_value=[])
        
        mock_assertion = MagicMock(return_value=(True, None))
        
        with patch('microsoft_agents.testing.utils.populate_activity') as mock_populate:
            mock_populate.side_effect = lambda act, defaults: act
            with patch('microsoft_agents.testing.utils.update_with_defaults') as mock_update:
                with patch('microsoft_agents.testing.assertions.ActivityAssertion.from_config', return_value=mock_assertion):
                    await ddt.run(agent_client, response_client)
        
        # Verify update_with_defaults was called
        mock_update.assert_called_once()
        call_args = mock_update.call_args[0]
        assert "assertion" in call_args[0] or "type" in call_args[0]
        assert call_args[1] == {"quantifier": "all"}

    @pytest.mark.asyncio
    async def test_run_populates_activity_with_defaults(self):
        """Test that run calls populate_activity with input defaults."""
        test_flow = {
            "defaults": {
                "input": {"locale": "en-US"}
            },
            "test": [
                {"type": "input", "type": "message", "text": "Hello"}
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        
        with patch('microsoft_agents.testing.utils.populate_activity') as mock_populate:
            mock_populate.side_effect = lambda act, defaults: act
            await ddt.run(agent_client, response_client)
        
        mock_populate.assert_called_once()
        call_args = mock_populate.call_args[0]
        assert isinstance(call_args[0], Activity)
        assert call_args[1] == {"locale": "en-US"}


class TestDataDrivenTestIntegration:
    """Integration tests for DataDrivenTest."""

    @pytest.mark.asyncio
    async def test_full_test_flow(self):
        """Test a complete test flow with all step types."""
        test_flow = {
            "description": "Complete integration test",
            "defaults": {
                "input": {"type": "message", "locale": "en-US"},
                "assertion": {"quantifier": "all"},
                "sleep": {"duration": 0.1}
            },
            "test": [
                {"type": "input", "text": "Hello"},
                {"type": "sleep"},
                {"type": "input", "text": "World"},
                {"type": "assertion", "assertion": {"type": "message"}},
            ]
        }
        ddt = DataDrivenTest(test_flow)
        
        agent_client = AsyncMock(spec=AgentClient)
        response_client = AsyncMock(spec=ResponseClient)
        response_client.pop = AsyncMock(return_value=[
            Activity(type="message", text="Response 1"),
            Activity(type="message", text="Response 2")
        ])
        
        mock_assertion = MagicMock(return_value=(True, None))
        
        with patch('microsoft_agents.testing.utils.populate_activity') as mock_populate:
            mock_populate.side_effect = lambda act, defaults: act
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with patch('microsoft_agents.testing.assertions.ActivityAssertion.from_config', return_value=mock_assertion):
                    await ddt.run(agent_client, response_client)
        
        assert agent_client.send_activity.call_count == 2
        assert response_client.pop.call_count == 1
        assert mock_assertion.call_count == 1