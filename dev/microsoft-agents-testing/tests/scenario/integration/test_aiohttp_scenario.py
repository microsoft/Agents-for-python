"""
Configuration and integration tests for AiohttpScenario.

This module demonstrates different configuration patterns for AiohttpScenario:
- Default configuration
- Custom response server ports
- JWT middleware enabled/disabled
- Custom client configurations
- Custom activity templates
- Multi-user scenarios
- Accessing agent environment
"""

import pytest
from unittest.mock import AsyncMock

from microsoft_agents.testing.scenario import (
    AiohttpScenario,
    ScenarioConfig,
    ClientConfig,
)
from microsoft_agents.testing.scenario.aiohttp_scenario import AgentEnvironment
from microsoft_agents.testing.utils import ActivityTemplate


# =============================================================================
# Sample Agent Initializers
# =============================================================================

async def echo_agent_init(env):
    """Initialize a simple echo agent."""
    @env.agent_application.activity("message")
    async def on_message(context, state):
        await context.send_activity(f"Echo: {context.activity.text}")


async def greeting_agent_init(env):
    """Initialize a greeting agent."""
    @env.agent_application.activity("message")
    async def on_message(context, state):
        user_name = context.activity.from_property.name or "User"
        await context.send_activity(f"Hello, {user_name}!")


async def noop_agent_init(env):
    """Initialize a no-op agent for testing."""
    pass


# =============================================================================
# Configuration Variation Tests
# =============================================================================

class TestAiohttpScenarioConfigurations:
    """Test different AiohttpScenario configurations."""
    
    def test_default_configuration(self):
        """Test AiohttpScenario with default configuration."""
        scenario = AiohttpScenario(init_agent=noop_agent_init)
        
        assert scenario._config.env_file_path == ".env"
        assert scenario._config.callback_server_port == 9378
        assert scenario._use_jwt_middleware is True
    
    def test_jwt_middleware_disabled(self):
        """Test AiohttpScenario with JWT middleware disabled."""
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            use_jwt_middleware=False
        )
        
        assert scenario._use_jwt_middleware is False
    
    def test_jwt_middleware_enabled(self):
        """Test AiohttpScenario with JWT middleware explicitly enabled."""
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            use_jwt_middleware=True
        )
        
        assert scenario._use_jwt_middleware is True
    
    def test_custom_env_file(self):
        """Test with custom .env file."""
        config = ScenarioConfig(env_file_path=".env.test")
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config
        )
        
        assert scenario._config.env_file_path == ".env.test"
    
    def test_custom_response_port(self):
        """Test with custom response server port."""
        config = ScenarioConfig(callback_server_port=9500)
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config
        )
        
        assert scenario._config.callback_server_port == 9500
    
    def test_custom_client_config(self):
        """Test with custom client configuration."""
        client_config = ClientConfig(
            user_id="test-user",
            user_name="Test User",
            headers={"X-Test": "value"}
        )
        config = ScenarioConfig(client_config=client_config)
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config
        )
        
        assert scenario._config.client_config.user_id == "test-user"
        assert scenario._config.client_config.headers["X-Test"] == "value"
    
    def test_custom_activity_template(self):
        """Test with custom activity template."""
        template = ActivityTemplate(
            channel_id="test-channel",
            locale="en-US"
        )
        config = ScenarioConfig(activity_template=template)
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config
        )
        
        assert scenario._config.activity_template is template
    
    def test_full_custom_configuration(self):
        """Test with fully customized configuration."""
        client_config = ClientConfig(
            user_id="power-user",
            user_name="Power User",
            headers={"X-Priority": "high"},
        )
        template = ActivityTemplate(
            channel_id="custom-channel",
        )
        config = ScenarioConfig(
            env_file_path=".env.custom",
            callback_server_port=9999,
            client_config=client_config,
            activity_template=template,
        )
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config,
            use_jwt_middleware=False,
        )
        
        assert scenario._config.env_file_path == ".env.custom"
        assert scenario._config.callback_server_port == 9999
        assert scenario._config.client_config.user_id == "power-user"
        assert scenario._use_jwt_middleware is False


# =============================================================================
# Different Agent Initializer Patterns
# =============================================================================

class TestAiohttpScenarioAgentInitPatterns:
    """Test different patterns for agent initialization."""
    
    def test_with_async_function(self):
        """Test with standard async function."""
        scenario = AiohttpScenario(init_agent=echo_agent_init)
        assert scenario._init_agent is echo_agent_init
    
    def test_with_async_mock(self):
        """Test with AsyncMock for testing."""
        mock_init = AsyncMock()
        scenario = AiohttpScenario(init_agent=mock_init)
        assert scenario._init_agent is mock_init
    
    def test_with_lambda_wrapper(self):
        """Test with async lambda-like wrapper."""
        async def custom_echo(env):
            @env.agent_application.activity("message")
            async def handler(ctx):
                await ctx.send_activity(f"Custom: {ctx.activity.text}")
        
        scenario = AiohttpScenario(init_agent=custom_echo)
        assert scenario._init_agent is custom_echo
    
    def test_with_noop_agent(self):
        """Test with no-op agent for minimal scenarios."""
        scenario = AiohttpScenario(init_agent=noop_agent_init)
        assert scenario._init_agent is noop_agent_init


# =============================================================================
# JWT Middleware Configuration Patterns
# =============================================================================

class TestAiohttpScenarioJwtMiddlewarePatterns:
    """Test JWT middleware configuration patterns."""
    
    def test_production_like_with_jwt(self):
        """Test production-like configuration with JWT enabled."""
        config = ScenarioConfig(env_file_path=".env.production")
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config,
            use_jwt_middleware=True  # Production should validate JWTs
        )
        
        assert scenario._use_jwt_middleware is True
    
    def test_development_without_jwt(self):
        """Test development configuration without JWT validation."""
        config = ScenarioConfig(env_file_path=".env.development")
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config,
            use_jwt_middleware=False  # Dev can skip JWT for easier testing
        )
        
        assert scenario._use_jwt_middleware is False
    
    def test_integration_test_without_jwt(self):
        """Test integration test configuration without JWT."""
        config = ScenarioConfig(
            env_file_path=".env.test",
            callback_server_port=9400,
        )
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config,
            use_jwt_middleware=False  # Tests often skip JWT
        )
        
        assert scenario._use_jwt_middleware is False
        assert scenario._config.callback_server_port == 9400


# =============================================================================
# Multi-User Configuration Patterns
# =============================================================================

class TestAiohttpScenarioMultiUserPatterns:
    """Test configurations for multi-user scenarios."""
    
    def test_default_user(self):
        """Test default user configuration."""
        scenario = AiohttpScenario(init_agent=noop_agent_init)
        
        assert scenario._config.client_config.user_id == "user-id"
        assert scenario._config.client_config.user_name == "User"
    
    def test_custom_default_user(self):
        """Test custom default user for all clients."""
        client_config = ClientConfig(
            user_id="admin",
            user_name="Administrator"
        )
        config = ScenarioConfig(client_config=client_config)
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config
        )
        
        assert scenario._config.client_config.user_id == "admin"
    
    def test_prepare_multi_user_configs(self):
        """Demonstrate preparing configs for multi-user testing."""
        # Create base scenario
        scenario = AiohttpScenario(init_agent=noop_agent_init)
        
        # Prepare different user configs to use with factory.create_client()
        users = {
            "alice": ClientConfig().with_user("alice", "Alice Smith"),
            "bob": ClientConfig().with_user("bob", "Bob Jones"),
            "charlie": ClientConfig().with_user("charlie", "Charlie Brown"),
        }
        
        # Verify all users are configured correctly
        assert users["alice"].user_id == "alice"
        assert users["bob"].user_name == "Bob Jones"
        assert users["charlie"].user_id == "charlie"
    
    def test_user_with_custom_headers(self):
        """Test user config with custom headers."""
        client_config = ClientConfig(
            user_id="api-user",
            user_name="API User"
        ).with_headers(**{"X-API-Key": "secret-key"})
        
        config = ScenarioConfig(client_config=client_config)
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            config=config
        )
        
        assert scenario._config.client_config.headers["X-API-Key"] == "secret-key"


# =============================================================================
# Environment Access Pattern Tests
# =============================================================================

class TestAiohttpScenarioEnvironmentPatterns:
    """Test agent environment access patterns."""
    
    def test_environment_not_available_before_run(self):
        """Test that environment is not available before running."""
        scenario = AiohttpScenario(init_agent=noop_agent_init)
        
        with pytest.raises(RuntimeError):
            _ = scenario.agent_environment
    
    def test_environment_stores_none_initially(self):
        """Test that _env is None before running."""
        scenario = AiohttpScenario(init_agent=noop_agent_init)
        
        assert scenario._env is None


# =============================================================================
# Comparison: AiohttpScenario vs ExternalScenario Configuration
# =============================================================================

class TestScenarioConfigurationComparison:
    """Compare configuration patterns between scenario types."""
    
    def test_same_config_works_for_both(self):
        """Test that same ScenarioConfig works for both scenario types."""
        from microsoft_agents.testing.scenario import ExternalScenario
        
        shared_config = ScenarioConfig(
            env_file_path=".env.shared",
            callback_server_port=9400,
            client_config=ClientConfig(user_id="shared-user"),
        )
        
        # Create both scenarios with same config
        aiohttp = AiohttpScenario(
            init_agent=noop_agent_init,
            config=shared_config
        )
        external = ExternalScenario(
            endpoint="http://localhost:3978/api/messages",
            config=shared_config
        )
        
        # Both should have the same configuration
        assert aiohttp._config.env_file_path == external._config.env_file_path
        assert aiohttp._config.callback_server_port == external._config.callback_server_port
        assert aiohttp._config.client_config.user_id == external._config.client_config.user_id
    
    def test_aiohttp_specific_option(self):
        """Test AiohttpScenario-specific option (JWT middleware)."""
        # AiohttpScenario has use_jwt_middleware option
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            use_jwt_middleware=False
        )
        
        assert scenario._use_jwt_middleware is False
        # ExternalScenario doesn't have this option - it connects to external agent
    
    def test_external_specific_option(self):
        """Test ExternalScenario-specific option (endpoint)."""
        from microsoft_agents.testing.scenario import ExternalScenario
        
        # ExternalScenario requires endpoint
        scenario = ExternalScenario(
            endpoint="https://my-agent.azurewebsites.net/api/messages"
        )
        
        assert "azurewebsites.net" in scenario._endpoint
        # AiohttpScenario doesn't need endpoint - it hosts the agent internally


# =============================================================================
# Full Integration Tests (Using Agent Runtime)
# =============================================================================

class TestAiohttpScenarioIntegration:
    """
    Integration tests for AiohttpScenario using the agent runtime.
    
    These tests spin up a real agent in-process and test the full scenario flow.
    """
    
    @pytest.mark.asyncio
    async def test_basic_echo_agent(self):
        """Test basic echo agent scenario."""
        scenario = AiohttpScenario(
            init_agent=echo_agent_init,
            use_jwt_middleware=False  # Disable for testing
        )
        
        async with scenario.client() as client:
            responses = await client.send("Hello, Agent!", wait=0.1)
            assert len(responses) > 0
            assert "Echo:" in responses[-1].text
    
    @pytest.mark.asyncio
    async def test_greeting_agent_with_user(self):
        """Test greeting agent with custom user."""
        config = ScenarioConfig(
            client_config=ClientConfig(user_id="alice", user_name="Alice")
        )
        scenario = AiohttpScenario(
            init_agent=greeting_agent_init,
            config=config,
            use_jwt_middleware=False
        )
        
        async with scenario.client() as client:
            responses = await client.send("Hi!", wait=0.1)
            assert len(responses) > 0
            assert "Alice" in responses[-1].text
    
    @pytest.mark.asyncio
    async def test_multi_user_with_factory(self):
        """Test multi-user scenario using client factory."""
        scenario = AiohttpScenario(
            init_agent=greeting_agent_init,
            use_jwt_middleware=False
        )
        
        async with scenario.run() as factory:
            alice = await factory.create_client(
                ClientConfig().with_user("alice", "Alice")
            )
            bob = await factory.create_client(
                ClientConfig().with_user("bob", "Bob")
            )
            
            alice_response = await alice.send("Hello!", wait=0.1)
            bob_response = await bob.send("Hello!", wait=0.1)
            
            assert "Alice" in alice_response[-1].text
            assert "Bob" in bob_response[-1].text
    
    @pytest.mark.asyncio
    async def test_access_agent_environment(self):
        """Test accessing agent environment during run."""
        scenario = AiohttpScenario(
            init_agent=noop_agent_init,
            use_jwt_middleware=False
        )
        
        async with scenario.run() as factory:
            env = scenario.agent_environment
            
            # Environment should be available now
            assert env is not None
            assert env.storage is not None
            assert env.agent_application is not None