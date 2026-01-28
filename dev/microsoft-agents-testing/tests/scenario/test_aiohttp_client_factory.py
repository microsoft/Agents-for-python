"""
Unit tests for the AiohttpClientFactory class.

This module tests:
- AiohttpClientFactory initialization
- Client creation with default config
- Client creation with custom config
- Session tracking and cleanup
- Auth token handling
- Header building
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession

from microsoft_agents.testing.scenario.aiohttp_client_factory import AiohttpClientFactory
from microsoft_agents.testing.scenario.client_config import ClientConfig
from microsoft_agents.testing.transcript import Transcript
from microsoft_agents.testing.utils import ActivityTemplate


# =============================================================================
# Helper Functions
# =============================================================================

def create_factory(
    agent_url: str = "http://localhost:3978/",
    response_endpoint: str = "http://localhost:9378/callback",
    sdk_config: dict | None = None,
    default_template: ActivityTemplate | None = None,
    default_config: ClientConfig | None = None,
    transcript: Transcript | None = None,
) -> AiohttpClientFactory:
    """Create an AiohttpClientFactory with sensible defaults for testing."""
    return AiohttpClientFactory(
        agent_url=agent_url,
        response_endpoint=response_endpoint,
        sdk_config=sdk_config or {},
        default_template=default_template or ActivityTemplate(),
        default_config=default_config or ClientConfig(),
        transcript=transcript or Transcript(),
    )


# =============================================================================
# AiohttpClientFactory Initialization Tests
# =============================================================================

class TestAiohttpClientFactoryInit:
    """Test AiohttpClientFactory initialization."""
    
    def test_init_stores_agent_url(self):
        factory = create_factory(agent_url="http://myagent:3978/")
        
        assert factory._agent_url == "http://myagent:3978/"
    
    def test_init_stores_response_endpoint(self):
        factory = create_factory(response_endpoint="http://localhost:9000/callback")
        
        assert factory._response_endpoint == "http://localhost:9000/callback"
    
    def test_init_stores_sdk_config(self):
        config = {"client_id": "abc123", "tenant_id": "xyz789"}
        factory = create_factory(sdk_config=config)
        
        assert factory._sdk_config == config
    
    def test_init_stores_default_template(self):
        template = ActivityTemplate(type="message")
        factory = create_factory(default_template=template)
        
        assert factory._default_template is template
    
    def test_init_stores_default_config(self):
        config = ClientConfig(user_id="alice")
        factory = create_factory(default_config=config)
        
        assert factory._default_config is config
    
    def test_init_stores_transcript(self):
        transcript = Transcript()
        factory = create_factory(transcript=transcript)
        
        assert factory._transcript is transcript
    
    def test_init_creates_empty_sessions_list(self):
        factory = create_factory()
        
        assert factory._sessions == []
        assert isinstance(factory._sessions, list)


# =============================================================================
# Default Config Usage Tests
# =============================================================================

class TestAiohttpClientFactoryDefaultConfig:
    """Test default config behavior."""
    
    def test_factory_stores_default_client_config(self):
        default_config = ClientConfig(user_id="default-user", user_name="Default")
        factory = create_factory(default_config=default_config)
        
        assert factory._default_config.user_id == "default-user"
        assert factory._default_config.user_name == "Default"
    
    def test_factory_stores_default_template(self):
        default_template = ActivityTemplate(type="message", text="hello")
        factory = create_factory(default_template=default_template)
        
        assert factory._default_template is default_template


# =============================================================================
# Session Tracking Tests
# =============================================================================

class TestAiohttpClientFactorySessionTracking:
    """Test session tracking behavior."""
    
    def test_sessions_list_starts_empty(self):
        factory = create_factory()
        
        assert len(factory._sessions) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_clears_sessions_list(self):
        factory = create_factory()
        
        # Add a mock session to the list
        mock_session = MagicMock(spec=ClientSession)
        mock_session.close = AsyncMock()
        factory._sessions.append(mock_session)
        
        await factory.cleanup()
        
        assert len(factory._sessions) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_closes_all_sessions(self):
        factory = create_factory()
        
        # Add multiple mock sessions
        mock_sessions = []
        for _ in range(3):
            mock_session = MagicMock(spec=ClientSession)
            mock_session.close = AsyncMock()
            factory._sessions.append(mock_session)
            mock_sessions.append(mock_session)
        
        await factory.cleanup()
        
        # Verify each session was closed
        for mock_session in mock_sessions:
            mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_with_no_sessions(self):
        factory = create_factory()
        
        # Should not raise
        await factory.cleanup()
        
        assert len(factory._sessions) == 0


# =============================================================================
# SDK Config Tests
# =============================================================================

class TestAiohttpClientFactorySdkConfig:
    """Test SDK configuration handling."""
    
    def test_empty_sdk_config(self):
        factory = create_factory(sdk_config={})
        
        assert factory._sdk_config == {}
    
    def test_sdk_config_with_credentials(self):
        sdk_config = {
            "client_id": "my-client-id",
            "client_secret": "my-secret",
            "tenant_id": "my-tenant",
        }
        factory = create_factory(sdk_config=sdk_config)
        
        assert factory._sdk_config["client_id"] == "my-client-id"
        assert factory._sdk_config["client_secret"] == "my-secret"
        assert factory._sdk_config["tenant_id"] == "my-tenant"


# =============================================================================
# Endpoint Configuration Tests
# =============================================================================

class TestAiohttpClientFactoryEndpoints:
    """Test endpoint configuration."""
    
    def test_localhost_agent_url(self):
        factory = create_factory(agent_url="http://localhost:3978/")
        
        assert factory._agent_url == "http://localhost:3978/"
    
    def test_https_agent_url(self):
        factory = create_factory(agent_url="https://my-agent.azurewebsites.net/")
        
        assert factory._agent_url == "https://my-agent.azurewebsites.net/"
    
    def test_response_endpoint_with_port(self):
        factory = create_factory(response_endpoint="http://localhost:9378/callback")
        
        assert factory._response_endpoint == "http://localhost:9378/callback"
    
    def test_different_ports_for_agent_and_callback(self):
        factory = create_factory(
            agent_url="http://localhost:3978/",
            response_endpoint="http://localhost:9000/callback"
        )
        
        assert factory._agent_url == "http://localhost:3978/"
        assert factory._response_endpoint == "http://localhost:9000/callback"


# =============================================================================
# ClientConfig Integration Tests
# =============================================================================

class TestAiohttpClientFactoryClientConfig:
    """Test ClientConfig integration."""
    
    def test_default_config_has_no_auth_token(self):
        factory = create_factory(default_config=ClientConfig())
        
        assert factory._default_config.auth_token is None
    
    def test_default_config_with_auth_token(self):
        config = ClientConfig(auth_token="pre-generated-token")
        factory = create_factory(default_config=config)
        
        assert factory._default_config.auth_token == "pre-generated-token"
    
    def test_default_config_with_custom_headers(self):
        config = ClientConfig(headers={"X-Custom": "value"})
        factory = create_factory(default_config=config)
        
        assert factory._default_config.headers == {"X-Custom": "value"}
    
    def test_default_config_with_user_identity(self):
        config = ClientConfig(user_id="alice", user_name="Alice Smith")
        factory = create_factory(default_config=config)
        
        assert factory._default_config.user_id == "alice"
        assert factory._default_config.user_name == "Alice Smith"


# =============================================================================
# Edge Cases
# =============================================================================

class TestAiohttpClientFactoryEdgeCases:
    """Test edge cases for AiohttpClientFactory."""
    
    def test_empty_agent_url(self):
        factory = create_factory(agent_url="")
        assert factory._agent_url == ""
    
    def test_none_sdk_config_values(self):
        factory = create_factory(sdk_config={"key": None})
        assert factory._sdk_config == {"key": None}
    
    @pytest.mark.asyncio
    async def test_multiple_cleanup_calls(self):
        factory = create_factory()
        
        # Should not raise even when called multiple times
        await factory.cleanup()
        await factory.cleanup()
        await factory.cleanup()
        
        assert len(factory._sessions) == 0
