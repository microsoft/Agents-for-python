"""
Unit tests for the Scenario base class.

This module tests:
- Scenario initialization
- Default config handling
- Abstract method requirements
- Client convenience method
"""

import pytest
from abc import ABC
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from microsoft_agents.testing.scenario.scenario import (
    Scenario,
    ScenarioConfig,
    ClientFactory,
)
from microsoft_agents.testing.scenario.client_config import ClientConfig
from microsoft_agents.testing.client import AgentClient


# =============================================================================
# Concrete Scenario Implementation for Testing
# =============================================================================

class MockAgentClient:
    """A simple mock client for testing."""
    def __init__(self, config: ClientConfig | None = None):
        self.config = config


class ConcreteClientFactory:
    """A concrete ClientFactory implementation for testing."""
    
    def __init__(self, default_config: ClientConfig | None = None):
        self._default_config = default_config or ClientConfig()
        self.clients_created: list[MockAgentClient] = []
    
    async def create_client(self, config: ClientConfig | None = None) -> MockAgentClient:
        """Create a mock client."""
        effective_config = config or self._default_config
        client = MockAgentClient(effective_config)
        self.clients_created.append(client)
        return client


class ConcreteScenario(Scenario):
    """A concrete Scenario implementation for testing."""
    
    def __init__(self, config: ScenarioConfig | None = None):
        super().__init__(config)
        self._factory: ConcreteClientFactory | None = None
        self.run_called = False
        self.run_exited = False
    
    @asynccontextmanager
    async def run(self) -> AsyncIterator[ConcreteClientFactory]:
        """Start the scenario and yield a factory."""
        self.run_called = True
        self._factory = ConcreteClientFactory(self._config.client_config)
        try:
            yield self._factory
        finally:
            self.run_exited = True


# =============================================================================
# Scenario Initialization Tests
# =============================================================================

class TestScenarioInit:
    """Test Scenario initialization."""
    
    def test_init_with_default_config(self):
        scenario = ConcreteScenario()
        
        assert scenario._config is not None
        assert isinstance(scenario._config, ScenarioConfig)
    
    def test_init_with_custom_config(self):
        custom_config = ScenarioConfig(env_file_path=".env.test")
        scenario = ConcreteScenario(config=custom_config)
        
        assert scenario._config is custom_config
        assert scenario._config.env_file_path == ".env.test"
    
    def test_init_with_none_creates_default_config(self):
        scenario = ConcreteScenario(config=None)
        
        assert scenario._config is not None
        assert scenario._config.env_file_path == ".env"


# =============================================================================
# Scenario Abstract Class Tests
# =============================================================================

class TestScenarioAbstract:
    """Test Scenario is properly abstract."""
    
    def test_scenario_is_abstract(self):
        assert issubclass(Scenario, ABC)
    
    def test_cannot_instantiate_base_scenario(self):
        with pytest.raises(TypeError) as exc_info:
            Scenario()
        
        assert "abstract" in str(exc_info.value).lower()
    
    def test_run_is_abstract_method(self):
        # The run method should be abstract
        assert hasattr(Scenario.run, '__isabstractmethod__')
        assert Scenario.run.__isabstractmethod__ is True


# =============================================================================
# Scenario.run() Context Manager Tests
# =============================================================================

class TestScenarioRun:
    """Test the run() context manager."""
    
    @pytest.mark.asyncio
    async def test_run_yields_client_factory(self):
        scenario = ConcreteScenario()
        
        async with scenario.run() as factory:
            assert factory is not None
            assert isinstance(factory, ConcreteClientFactory)
    
    @pytest.mark.asyncio
    async def test_run_sets_run_called_flag(self):
        scenario = ConcreteScenario()
        
        async with scenario.run():
            assert scenario.run_called is True
    
    @pytest.mark.asyncio
    async def test_run_sets_run_exited_flag_on_exit(self):
        scenario = ConcreteScenario()
        
        async with scenario.run():
            assert scenario.run_exited is False
        
        assert scenario.run_exited is True
    
    @pytest.mark.asyncio
    async def test_run_exits_on_exception(self):
        scenario = ConcreteScenario()
        
        with pytest.raises(ValueError):
            async with scenario.run():
                raise ValueError("Test exception")
        
        assert scenario.run_exited is True
    
    @pytest.mark.asyncio
    async def test_factory_can_create_multiple_clients(self):
        scenario = ConcreteScenario()
        
        async with scenario.run() as factory:
            client1 = await factory.create_client()
            client2 = await factory.create_client()
            client3 = await factory.create_client()
            
            assert len(factory.clients_created) == 3
    
    @pytest.mark.asyncio
    async def test_factory_uses_custom_config(self):
        scenario = ConcreteScenario()
        custom_config = ClientConfig(user_id="alice", user_name="Alice")
        
        async with scenario.run() as factory:
            client = await factory.create_client(custom_config)
            
            assert client.config.user_id == "alice"
            assert client.config.user_name == "Alice"


# =============================================================================
# Scenario.client() Convenience Method Tests
# =============================================================================

class TestScenarioClient:
    """Test the client() convenience method."""
    
    @pytest.mark.asyncio
    async def test_client_yields_single_client(self):
        scenario = ConcreteScenario()
        
        async with scenario.client() as client:
            assert client is not None
            assert isinstance(client, MockAgentClient)
    
    @pytest.mark.asyncio
    async def test_client_calls_run_under_the_hood(self):
        scenario = ConcreteScenario()
        
        async with scenario.client():
            assert scenario.run_called is True
    
    @pytest.mark.asyncio
    async def test_client_with_custom_config(self):
        scenario = ConcreteScenario()
        custom_config = ClientConfig(user_id="bob", user_name="Bob")
        
        async with scenario.client(custom_config) as client:
            assert client.config.user_id == "bob"
            assert client.config.user_name == "Bob"
    
    @pytest.mark.asyncio
    async def test_client_uses_default_config_when_none(self):
        scenario_config = ScenarioConfig(
            client_config=ClientConfig(user_id="default-user")
        )
        scenario = ConcreteScenario(config=scenario_config)
        
        async with scenario.client() as client:
            assert client.config.user_id == "default-user"
    
    @pytest.mark.asyncio
    async def test_client_cleans_up_on_exit(self):
        scenario = ConcreteScenario()
        
        async with scenario.client():
            pass
        
        assert scenario.run_exited is True
    
    @pytest.mark.asyncio
    async def test_client_cleans_up_on_exception(self):
        scenario = ConcreteScenario()
        
        with pytest.raises(RuntimeError):
            async with scenario.client():
                raise RuntimeError("Test error")
        
        assert scenario.run_exited is True


# =============================================================================
# ClientFactory Protocol Tests
# =============================================================================

class TestClientFactoryProtocol:
    """Test the ClientFactory protocol."""
    
    def test_concrete_factory_satisfies_protocol(self):
        factory = ConcreteClientFactory()
        
        # Check that it has the required method
        assert hasattr(factory, 'create_client')
        assert callable(factory.create_client)
    
    @pytest.mark.asyncio
    async def test_create_client_returns_client(self):
        factory = ConcreteClientFactory()
        
        client = await factory.create_client()
        
        assert client is not None
    
    @pytest.mark.asyncio
    async def test_create_client_accepts_optional_config(self):
        factory = ConcreteClientFactory()
        
        # Should work with no config
        client1 = await factory.create_client()
        
        # Should work with config
        client2 = await factory.create_client(ClientConfig(user_id="custom"))
        
        assert client1 is not None
        assert client2 is not None
        assert client2.config.user_id == "custom"


# =============================================================================
# Multiple Scenarios Tests
# =============================================================================

class TestMultipleScenarios:
    """Test using multiple scenario instances."""
    
    def test_different_configs_are_independent(self):
        config1 = ScenarioConfig(env_file_path=".env.dev")
        config2 = ScenarioConfig(env_file_path=".env.prod")
        
        scenario1 = ConcreteScenario(config=config1)
        scenario2 = ConcreteScenario(config=config2)
        
        assert scenario1._config.env_file_path == ".env.dev"
        assert scenario2._config.env_file_path == ".env.prod"
    
    @pytest.mark.asyncio
    async def test_scenarios_run_independently(self):
        scenario1 = ConcreteScenario()
        scenario2 = ConcreteScenario()
        
        async with scenario1.run() as factory1:
            async with scenario2.run() as factory2:
                assert factory1 is not factory2
                assert scenario1.run_called is True
                assert scenario2.run_called is True
