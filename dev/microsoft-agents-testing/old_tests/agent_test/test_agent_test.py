# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import MagicMock, patch
from contextlib import asynccontextmanager
from dataclasses import dataclass

from microsoft_agents.testing.agent_test.agent_test import (
    _create_fixtures,
    agent_test,
)
from microsoft_agents.testing.agent_test.agent_scenario import AgentScenario
from microsoft_agents.testing.agent_test.aiohttp_agent_scenario import AgentEnvironment
from microsoft_agents.testing.agent_test.agent_client import AgentClient


# =============================================================================
# Test Helpers - Mock Scenarios
# =============================================================================

class MockAgentClient:
    """A mock agent client for testing."""
    
    def __init__(self, name: str = "mock_client"):
        self.name = name
        self.sent_messages = []
    
    async def send(self, message: str):
        self.sent_messages.append(message)
        return f"response to: {message}"


class BasicMockScenario(AgentScenario):
    """A basic mock scenario without agent_environment (simulates external agent)."""
    
    def __init__(self):
        # Skip parent init to avoid dotenv and config loading
        self._mock_client = None
    
    @asynccontextmanager
    async def client(self):
        self._mock_client = MockAgentClient("basic_client")
        yield self._mock_client


class MockAgentApplication:
    """Mock agent application."""
    def __init__(self):
        self.name = "MockAgentApp"


class MockAuthorization:
    """Mock authorization."""
    def __init__(self):
        self.is_authorized = True


class MockStorage:
    """Mock storage."""
    def __init__(self):
        self.data = {}


class MockAdapter:
    """Mock channel service adapter."""
    def __init__(self):
        self.name = "MockAdapter"


class MockConnections:
    """Mock connections manager."""
    def __init__(self):
        self.connections = []


@dataclass
class MockAgentEnvironment:
    """Mock agent environment matching AgentEnvironment structure."""
    config: dict
    agent_application: MockAgentApplication
    authorization: MockAuthorization
    adapter: MockAdapter
    storage: MockStorage
    connections: MockConnections


class AiohttpMockScenario(AgentScenario):
    """A mock scenario with agent_environment (simulates locally-hosted agent)."""
    
    def __init__(self):
        # Skip parent init to avoid dotenv and config loading
        self._mock_client = MockAgentClient("aiohttp_client")
        self._agent_environment = MockAgentEnvironment(
            config={"test_key": "test_value"},
            agent_application=MockAgentApplication(),
            authorization=MockAuthorization(),
            adapter=MockAdapter(),
            storage=MockStorage(),
            connections=MockConnections(),
        )
    
    @property
    def agent_environment(self) -> MockAgentEnvironment:
        return self._agent_environment
    
    @asynccontextmanager
    async def client(self):
        yield self._mock_client


# =============================================================================
# Tests for Basic Scenario (External Agent - no agent_environment)
# =============================================================================

@agent_test(BasicMockScenario())
class TestAgentTestWithBasicScenario:
    """Test class decorated with @agent_test using a basic scenario."""

    @pytest.mark.asyncio
    async def test_agent_client_fixture_is_available(self, agent_client):
        """Test that agent_client fixture is injected and usable."""
        assert agent_client is not None
        assert isinstance(agent_client, MockAgentClient)
        assert agent_client.name == "basic_client"

    @pytest.mark.asyncio
    async def test_can_send_message_via_agent_client(self, agent_client):
        """Test that we can use the agent_client to send messages."""
        response = await agent_client.send("Hello, agent!")
        
        assert response == "response to: Hello, agent!"
        assert "Hello, agent!" in agent_client.sent_messages

    @pytest.mark.asyncio
    async def test_agent_client_tracks_multiple_messages(self, agent_client):
        """Test that agent_client tracks multiple sent messages."""
        await agent_client.send("First message")
        await agent_client.send("Second message")
        
        assert len(agent_client.sent_messages) == 2
        assert agent_client.sent_messages[0] == "First message"
        assert agent_client.sent_messages[1] == "Second message"


# =============================================================================
# Tests for Aiohttp Scenario (Locally-hosted Agent - with agent_environment)
# =============================================================================

@agent_test(AiohttpMockScenario())
class TestAgentTestWithAiohttpScenario:
    """Test class decorated with @agent_test using an aiohttp scenario with agent_environment."""

    @pytest.mark.asyncio
    async def test_agent_client_fixture_is_available(self, agent_client):
        """Test that agent_client fixture is injected."""
        assert agent_client is not None
        assert isinstance(agent_client, MockAgentClient)
        assert agent_client.name == "aiohttp_client"

    def test_agent_environment_fixture_is_available(self, agent_client, agent_environment):
        """Test that agent_environment fixture is injected."""
        assert agent_environment is not None
        assert isinstance(agent_environment, MockAgentEnvironment)
        assert agent_environment.config == {"test_key": "test_value"}

    def test_agent_application_fixture_is_available(self, agent_client, agent_application):
        """Test that agent_application fixture is injected."""
        assert agent_application is not None
        assert isinstance(agent_application, MockAgentApplication)
        assert agent_application.name == "MockAgentApp"

    def test_authorization_fixture_is_available(self, agent_client, authorization):
        """Test that authorization fixture is injected."""
        assert authorization is not None
        assert isinstance(authorization, MockAuthorization)
        assert authorization.is_authorized is True

    def test_storage_fixture_is_available(self, agent_client, storage):
        """Test that storage fixture is injected."""
        assert storage is not None
        assert isinstance(storage, MockStorage)
        assert storage.data == {}

    def test_adapter_fixture_is_available(self, agent_client, adapter):
        """Test that adapter fixture is injected."""
        assert adapter is not None
        assert isinstance(adapter, MockAdapter)
        assert adapter.name == "MockAdapter"

    def test_connection_manager_fixture_is_available(self, agent_client, connection_manager):
        """Test that connection_manager fixture is injected."""
        assert connection_manager is not None
        assert isinstance(connection_manager, MockConnections)
        assert connection_manager.connections == []

    def test_can_modify_storage_in_test(self, agent_client, storage):
        """Test that we can interact with storage during tests."""
        storage.data["test_key"] = "test_value"
        
        assert storage.data["test_key"] == "test_value"

    def test_all_fixtures_come_from_same_environment(
        self, agent_client, agent_environment, agent_application, 
        authorization, storage, adapter, connection_manager
    ):
        """Test that all fixtures are consistent with the agent_environment."""
        assert agent_application is agent_environment.agent_application
        assert authorization is agent_environment.authorization
        assert storage is agent_environment.storage
        assert adapter is agent_environment.adapter
        assert connection_manager is agent_environment.connections


# =============================================================================
# Tests for Decorator Error Handling
# =============================================================================

class TestAgentTestDecoratorErrors:
    """Test error cases for the @agent_test decorator."""

    def test_raises_error_when_class_already_has_agent_client(self):
        """Test that decorator raises ValueError when class already has agent_client."""
        with pytest.raises(ValueError) as exc_info:
            @agent_test(BasicMockScenario())
            class TestClassWithExistingAgentClient:
                def agent_client(self):
                    pass
        
        assert "agent_client" in str(exc_info.value)
        assert "cannot decorate" in str(exc_info.value)

    def test_raises_error_when_class_already_has_agent_environment(self):
        """Test that decorator raises ValueError when class already has agent_environment."""
        with pytest.raises(ValueError) as exc_info:
            @agent_test(AiohttpMockScenario())
            class TestClassWithExistingAgentEnvironment:
                agent_environment = None
        
        assert "agent_environment" in str(exc_info.value)
        assert "cannot decorate" in str(exc_info.value)

    def test_raises_error_when_class_already_has_storage(self):
        """Test that decorator raises ValueError when class already has storage."""
        with pytest.raises(ValueError) as exc_info:
            @agent_test(AiohttpMockScenario())
            class TestClassWithExistingStorage:
                def storage(self):
                    return {}
        
        assert "storage" in str(exc_info.value)
        assert "cannot decorate" in str(exc_info.value)


# =============================================================================
# Tests for String Argument (External Agent Scenario)
# =============================================================================

class TestAgentTestWithStringArg:
    """Test the @agent_test decorator when given a string endpoint."""

    def test_creates_external_agent_scenario(self):
        """Test that passing a string creates an ExternalAgentScenario."""
        with patch("microsoft_agents.testing.agent_test.agent_test.ExternalAgentScenario") as mock_external, \
             patch("microsoft_agents.testing.agent_test.agent_test._create_fixtures") as mock_create_fixtures:
            
            mock_create_fixtures.return_value = []
            
            @agent_test("http://localhost:3978/api/messages")
            class TestClass:
                pass
            
            mock_external.assert_called_once_with("http://localhost:3978/api/messages")


# =============================================================================
# Tests for _create_fixtures Function
# =============================================================================

class TestCreateFixtures:
    """Test the _create_fixtures helper function."""

    def test_creates_only_agent_client_for_basic_scenario(self):
        """Test that only agent_client fixture is created for scenarios without agent_environment."""
        scenario = BasicMockScenario()
        
        fixtures = _create_fixtures(scenario)
        
        assert len(fixtures) == 1
        assert fixtures[0].__name__ == "agent_client"

    def test_creates_all_fixtures_for_aiohttp_scenario(self):
        """Test that all fixtures are created for scenarios with agent_environment."""
        scenario = AiohttpMockScenario()
        
        fixtures = _create_fixtures(scenario)
        
        fixture_names = [f.__name__ for f in fixtures]
        assert len(fixtures) == 7
        assert "agent_client" in fixture_names
        assert "agent_environment" in fixture_names
        assert "agent_application" in fixture_names
        assert "authorization" in fixture_names
        assert "storage" in fixture_names
        assert "adapter" in fixture_names
        assert "connection_manager" in fixture_names


# =============================================================================
# Tests for Decorator Preserving Class Behavior
# =============================================================================

@agent_test(BasicMockScenario())
class TestDecoratorPreservesClassBehavior:
    """Test that the decorator preserves existing class methods and attributes."""
    
    class_attribute = "original_value"
    
    def existing_method(self):
        return "existing_result"
    
    def test_class_attribute_preserved(self, agent_client):
        """Test that class attributes are preserved after decoration."""
        assert self.class_attribute == "original_value"
    
    def test_existing_method_preserved(self, agent_client):
        """Test that existing methods are preserved after decoration."""
        assert self.existing_method() == "existing_result"
    
    @pytest.mark.asyncio
    async def test_can_use_both_existing_and_fixture(self, agent_client):
        """Test that we can use both existing methods and fixtures together."""
        existing_result = self.existing_method()
        response = await agent_client.send(existing_result)
        
        assert response == "response to: existing_result"