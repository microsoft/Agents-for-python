"""
Unit tests for the AiohttpScenario class.

This module tests:
- AiohttpScenario initialization
- Validation of init_agent parameter
- Configuration handling
- JWT middleware configuration
- agent_environment property behavior

Note: Full integration tests require the microsoft_agents.hosting package
and a proper agent environment setup.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from microsoft_agents.testing.scenario.scenario import ScenarioConfig


# =============================================================================
# Test Helper: Create minimal async init_agent function
# =============================================================================

async def dummy_init_agent(env):
    """A minimal init_agent function for testing."""
    pass


# =============================================================================
# Conditional Import Tests
# =============================================================================

class TestAiohttpScenarioImport:
    """Test that AiohttpScenario can be imported."""
    
    def test_can_import_aiohttp_scenario(self):
        """Test that AiohttpScenario can be imported."""
        try:
            from microsoft_agents.testing.scenario.aiohttp_scenario import AiohttpScenario
            assert AiohttpScenario is not None
        except ImportError as e:
            pytest.skip(f"AiohttpScenario import requires additional dependencies: {e}")
    
    def test_can_import_agent_environment(self):
        """Test that AgentEnvironment can be imported."""
        try:
            from microsoft_agents.testing.scenario.aiohttp_scenario import AgentEnvironment
            assert AgentEnvironment is not None
        except ImportError as e:
            pytest.skip(f"AgentEnvironment import requires additional dependencies: {e}")


# =============================================================================
# Fixture for conditional testing
# =============================================================================

@pytest.fixture
def aiohttp_scenario_class():
    """Fixture that provides AiohttpScenario class if available."""
    try:
        from microsoft_agents.testing.scenario.aiohttp_scenario import AiohttpScenario
        return AiohttpScenario
    except ImportError as e:
        pytest.skip(f"AiohttpScenario requires additional dependencies: {e}")


@pytest.fixture
def agent_environment_class():
    """Fixture that provides AgentEnvironment class if available."""
    try:
        from microsoft_agents.testing.scenario.aiohttp_scenario import AgentEnvironment
        return AgentEnvironment
    except ImportError as e:
        pytest.skip(f"AgentEnvironment requires additional dependencies: {e}")


# =============================================================================
# AiohttpScenario Initialization Tests
# =============================================================================

class TestAiohttpScenarioInit:
    """Test AiohttpScenario initialization."""
    
    def test_init_with_init_agent_function(self, aiohttp_scenario_class):
        """Test initialization with an init_agent function."""
        scenario = aiohttp_scenario_class(init_agent=dummy_init_agent)
        
        assert scenario._init_agent is dummy_init_agent
    
    def test_init_with_custom_config(self, aiohttp_scenario_class):
        """Test initialization with custom config."""
        config = ScenarioConfig(env_file_path=".env.test")
        scenario = aiohttp_scenario_class(
            init_agent=dummy_init_agent,
            config=config
        )
        
        assert scenario._config.env_file_path == ".env.test"
    
    def test_init_with_default_config(self, aiohttp_scenario_class):
        """Test initialization uses default config when not provided."""
        scenario = aiohttp_scenario_class(init_agent=dummy_init_agent)
        
        assert scenario._config is not None
        assert isinstance(scenario._config, ScenarioConfig)
    
    def test_init_with_jwt_middleware_enabled_by_default(self, aiohttp_scenario_class):
        """Test that JWT middleware is enabled by default."""
        scenario = aiohttp_scenario_class(init_agent=dummy_init_agent)
        
        assert scenario._use_jwt_middleware is True
    
    def test_init_with_jwt_middleware_disabled(self, aiohttp_scenario_class):
        """Test initialization with JWT middleware disabled."""
        scenario = aiohttp_scenario_class(
            init_agent=dummy_init_agent,
            use_jwt_middleware=False
        )
        
        assert scenario._use_jwt_middleware is False
    
    def test_init_environment_is_none_before_run(self, aiohttp_scenario_class):
        """Test that _env is None before running the scenario."""
        scenario = aiohttp_scenario_class(init_agent=dummy_init_agent)
        
        assert scenario._env is None


# =============================================================================
# AiohttpScenario Validation Tests
# =============================================================================

class TestAiohttpScenarioValidation:
    """Test AiohttpScenario validation."""
    
    def test_raises_when_init_agent_is_none(self, aiohttp_scenario_class):
        """Test that ValueError is raised when init_agent is None."""
        with pytest.raises(ValueError) as exc_info:
            aiohttp_scenario_class(init_agent=None)
        
        assert "init_agent must be provided" in str(exc_info.value)
    
    def test_accepts_async_function_as_init_agent(self, aiohttp_scenario_class):
        """Test that async functions are accepted for init_agent."""
        async def async_init(env):
            pass
        
        scenario = aiohttp_scenario_class(init_agent=async_init)
        
        assert scenario._init_agent is async_init
    
    def test_accepts_async_mock_as_init_agent(self, aiohttp_scenario_class):
        """Test that AsyncMock can be used as init_agent."""
        mock_init = AsyncMock()
        
        scenario = aiohttp_scenario_class(init_agent=mock_init)
        
        assert scenario._init_agent is mock_init


# =============================================================================
# AiohttpScenario agent_environment Property Tests
# =============================================================================

class TestAiohttpScenarioAgentEnvironment:
    """Test the agent_environment property."""
    
    def test_agent_environment_raises_when_not_running(self, aiohttp_scenario_class):
        """Test that accessing agent_environment before running raises."""
        scenario = aiohttp_scenario_class(init_agent=dummy_init_agent)
        
        with pytest.raises(RuntimeError) as exc_info:
            _ = scenario.agent_environment
        
        assert "not available" in str(exc_info.value).lower() or \
               "is the scenario running" in str(exc_info.value).lower()
    
    def test_agent_environment_error_message_mentions_running(self, aiohttp_scenario_class):
        """Test that the error message mentions the scenario needs to be running."""
        scenario = aiohttp_scenario_class(init_agent=dummy_init_agent)
        
        with pytest.raises(RuntimeError) as exc_info:
            _ = scenario.agent_environment
        
        # The error should mention something about the scenario running
        error_message = str(exc_info.value).lower()
        assert "running" in error_message or "not available" in error_message


# =============================================================================
# AgentEnvironment Dataclass Tests
# =============================================================================

class TestAgentEnvironmentDataclass:
    """Test the AgentEnvironment dataclass."""
    
    def test_agent_environment_is_dataclass(self, agent_environment_class):
        """Test that AgentEnvironment is a dataclass."""
        from dataclasses import is_dataclass
        
        assert is_dataclass(agent_environment_class)
    
    def test_agent_environment_has_required_fields(self, agent_environment_class):
        """Test that AgentEnvironment has all required fields."""
        # Check field annotations
        annotations = agent_environment_class.__annotations__
        
        expected_fields = ['config', 'agent_application', 'authorization', 
                          'adapter', 'storage', 'connections']
        
        for field in expected_fields:
            assert field in annotations, f"Missing field: {field}"


# =============================================================================
# AiohttpScenario Configuration Tests
# =============================================================================

class TestAiohttpScenarioConfiguration:
    """Test configuration handling."""
    
    def test_config_port_is_accessible(self, aiohttp_scenario_class):
        """Test that config port settings are accessible."""
        config = ScenarioConfig(callback_server_port=9000)
        scenario = aiohttp_scenario_class(
            init_agent=dummy_init_agent,
            config=config
        )
        
        assert scenario._config.callback_server_port == 9000
    
    def test_config_env_file_path_is_accessible(self, aiohttp_scenario_class):
        """Test that config env file path is accessible."""
        config = ScenarioConfig(env_file_path="/path/to/.env")
        scenario = aiohttp_scenario_class(
            init_agent=dummy_init_agent,
            config=config
        )
        
        assert scenario._config.env_file_path == "/path/to/.env"


# =============================================================================
# AiohttpScenario Inheritance Tests
# =============================================================================

class TestAiohttpScenarioInheritance:
    """Test that AiohttpScenario properly inherits from Scenario."""
    
    def test_has_run_method(self, aiohttp_scenario_class):
        """Test that AiohttpScenario has a run method."""
        scenario = aiohttp_scenario_class(init_agent=dummy_init_agent)
        
        assert hasattr(scenario, 'run')
        assert callable(scenario.run)
    
    def test_has_client_method(self, aiohttp_scenario_class):
        """Test that AiohttpScenario has a client method."""
        scenario = aiohttp_scenario_class(init_agent=dummy_init_agent)
        
        assert hasattr(scenario, 'client')
        assert callable(scenario.client)


# =============================================================================
# Edge Cases
# =============================================================================

class TestAiohttpScenarioEdgeCases:
    """Test edge cases for AiohttpScenario."""
    
    def test_lambda_as_init_agent(self, aiohttp_scenario_class):
        """Test that lambda functions (wrapped) work as init_agent."""
        # Note: lambdas can't be async directly, so we test with a sync-looking
        # function that's actually async
        async def lambda_like_init(env):
            return None
        
        scenario = aiohttp_scenario_class(init_agent=lambda_like_init)
        assert scenario._init_agent is lambda_like_init
    
    def test_jwt_middleware_bool_values(self, aiohttp_scenario_class):
        """Test different bool values for use_jwt_middleware."""
        scenario_true = aiohttp_scenario_class(
            init_agent=dummy_init_agent,
            use_jwt_middleware=True
        )
        scenario_false = aiohttp_scenario_class(
            init_agent=dummy_init_agent,
            use_jwt_middleware=False
        )
        
        assert scenario_true._use_jwt_middleware is True
        assert scenario_false._use_jwt_middleware is False
