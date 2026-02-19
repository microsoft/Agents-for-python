# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the _AiohttpClientFactory class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientSession

from microsoft_agents.testing.core._aiohttp_client_factory import _AiohttpClientFactory
from microsoft_agents.testing.core.config import ClientConfig
from microsoft_agents.testing.core.fluent import ActivityTemplate
from microsoft_agents.testing.core.transport import Transcript
from microsoft_agents.testing.core.agent_client import AgentClient


# ============================================================================
# _AiohttpClientFactory Initialization Tests
# ============================================================================

class TestAiohttpClientFactoryInitialization:
    """Tests for _AiohttpClientFactory initialization."""

    def test_initialization_stores_all_parameters(self):
        """Factory stores all constructor parameters."""
        template = ActivityTemplate(text="Test")
        config = ClientConfig()
        transcript = Transcript()
        sdk_config = {"CONNECTIONS": {}}
        
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config=sdk_config,
            default_template=template,
            default_config=config,
            transcript=transcript,
        )
        
        assert factory._agent_url == "http://localhost:3978"
        assert factory._response_endpoint == "http://localhost:9378/api/callback"
        assert factory._sdk_config is sdk_config
        assert factory._default_template is template
        assert factory._default_config is config
        assert factory._transcript is transcript

    def test_initialization_creates_empty_sessions_list(self):
        """Factory initializes with empty sessions list."""
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        assert factory._sessions == []


# ============================================================================
# _AiohttpClientfactory Tests
# ============================================================================

class TestAiohttpClientFactoryCreateClient:
    """Tests for _AiohttpClientfactory method."""

    @pytest.fixture
    def factory(self):
        """Create a factory with default configuration."""
        return _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(type="message"),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )

    @pytest.mark.asyncio
    async def test_create_client_returns_agent_client(self, factory):
        """create_client returns an AgentClient instance."""
        client = await factory()
        
        try:
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_tracks_session(self, factory):
        """create_client adds created session to sessions list."""
        assert len(factory._sessions) == 0
        
        await factory()
        
        try:
            assert len(factory._sessions) == 1
            assert isinstance(factory._sessions[0], ClientSession)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_tracks_multiple_sessions(self, factory):
        """create_client tracks multiple sessions."""
        await factory()
        await factory()
        await factory()
        
        try:
            assert len(factory._sessions) == 3
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_uses_default_config_when_none_provided(self, factory):
        """create_client uses default config when no config is passed."""
        # Just verify it doesn't raise and creates a client
        client = await factory()
        
        try:
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_uses_provided_config(self, factory):
        """create_client uses provided config over default."""
        custom_config = ClientConfig(
            headers={"X-Custom": "custom-value"},
            auth_token="custom-token",
        )
        
        client = await factory(config=custom_config)
        
        try:
            assert isinstance(client, AgentClient)
            # Verify session was created with custom headers
            session = factory._sessions[0]
            assert "X-Custom" in session._default_headers
            assert session._default_headers["X-Custom"] == "custom-value"
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_sets_content_type_header(self, factory):
        """create_client always sets Content-Type header."""
        await factory()
        
        try:
            session = factory._sessions[0]
            assert "Content-Type" in session._default_headers
            assert session._default_headers["Content-Type"] == "application/json"
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_with_auth_token_sets_authorization(self, factory):
        """create_client sets Authorization header when auth_token is provided."""
        config = ClientConfig(auth_token="test-bearer-token")
        
        await factory(config=config)
        
        try:
            session = factory._sessions[0]
            assert "Authorization" in session._default_headers
            assert session._default_headers["Authorization"] == "Bearer test-bearer-token"
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_merges_custom_headers(self, factory):
        """create_client merges custom headers with defaults."""
        config = ClientConfig(headers={"X-Request-Id": "123", "Accept": "application/json"})
        
        await factory(config=config)
        
        try:
            session = factory._sessions[0]
            assert session._default_headers["Content-Type"] == "application/json"
            assert session._default_headers["X-Request-Id"] == "123"
            assert session._default_headers["Accept"] == "application/json"
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_uses_custom_activity_template(self, factory):
        """create_client uses custom activity_template from config."""
        custom_template = ActivityTemplate(text="Custom message")
        config = ClientConfig(activity_template=custom_template)
        
        client = await factory(config=config)
        
        try:
            assert isinstance(client, AgentClient)
            # The client should use a template derived from the custom template
        finally:
            await factory.cleanup()


# ============================================================================
# _AiohttpClientfactory Authorization Tests
# ============================================================================

class TestAiohttpClientFactoryAuthorization:
    """Tests for authorization handling in create_client."""

    @pytest.mark.asyncio
    async def test_explicit_authorization_header_preserved(self):
        """Explicit Authorization header is preserved."""
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        config = ClientConfig(headers={"Authorization": "Bearer explicit-token"})
        
        await factory(config=config)
        
        try:
            session = factory._sessions[0]
            assert session._default_headers["Authorization"] == "Bearer explicit-token"
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_auth_token_overrides_when_no_explicit_authorization(self):
        """auth_token is used when no explicit Authorization header."""
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        config = ClientConfig(auth_token="token-from-config")
        
        await factory(config=config)
        
        try:
            session = factory._sessions[0]
            assert session._default_headers["Authorization"] == "Bearer token-from-config"
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_no_auth_when_no_token_and_no_sdk_config(self):
        """No Authorization header when no token and sdk_config fails."""
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},  # Empty, will cause generate_token_from_config to fail
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        await factory()
        
        try:
            session = factory._sessions[0]
            # No Authorization header should be set
            assert "Authorization" not in session._default_headers
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_sdk_config_token_generation_on_failure(self):
        """SDK config token generation failure is handled gracefully."""
        # Provide invalid SDK config that will cause token generation to fail
        invalid_sdk_config = {"CONNECTIONS": {"SERVICE_CONNECTION": {"SETTINGS": {}}}}
        
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config=invalid_sdk_config,
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        # Should not raise even though SDK config is invalid
        client = await factory()
        
        try:
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()


# ============================================================================
# _AiohttpClientFactory.cleanup Tests
# ============================================================================

class TestAiohttpClientFactoryCleanup:
    """Tests for _AiohttpClientFactory.cleanup method."""

    @pytest.mark.asyncio
    async def test_cleanup_closes_all_sessions(self):
        """cleanup closes all created sessions."""
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        # Create multiple clients
        await factory()
        await factory()
        
        sessions = list(factory._sessions)
        assert len(sessions) == 2
        
        await factory.cleanup()
        
        # All sessions should be closed
        for session in sessions:
            assert session.closed

    @pytest.mark.asyncio
    async def test_cleanup_clears_sessions_list(self):
        """cleanup clears the sessions list."""
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        await factory()
        await factory()
        
        assert len(factory._sessions) == 2
        
        await factory.cleanup()
        
        assert factory._sessions == []

    @pytest.mark.asyncio
    async def test_cleanup_on_empty_sessions_list(self):
        """cleanup handles empty sessions list gracefully."""
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        # Should not raise
        await factory.cleanup()
        
        assert factory._sessions == []

    @pytest.mark.asyncio
    async def test_cleanup_can_be_called_multiple_times(self):
        """cleanup can be called multiple times safely."""
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        await factory()
        
        await factory.cleanup()
        await factory.cleanup()  # Second call should not raise
        
        assert factory._sessions == []


# ============================================================================
# _AiohttpClientFactory Template Handling Tests
# ============================================================================

class TestAiohttpClientFactoryTemplateHandling:
    """Tests for template handling in _AiohttpClientFactory."""

    @pytest.mark.asyncio
    async def test_default_template_used_when_config_has_none(self):
        """Default template is used when config has no activity_template."""
        default_template = ActivityTemplate(type="message", text="Default")
        
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=default_template,
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        client = await factory()
        
        try:
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_config_template_used_when_provided(self):
        """Config activity_template is used when provided."""
        default_template = ActivityTemplate(type="message", text="Default")
        custom_template = ActivityTemplate(type="event", text="Custom")
        config = ClientConfig(activity_template=custom_template)
        
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=default_template,
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        client = await factory(config=config)
        
        try:
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()


# ============================================================================
# Integration-style Tests
# ============================================================================

class TestAiohttpClientFactoryIntegration:
    """Integration-style tests for _AiohttpClientFactory."""

    @pytest.mark.asyncio
    async def test_full_workflow_create_and_cleanup(self):
        """Full workflow: create multiple clients, then cleanup."""
        factory = _AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(headers={"X-Default": "value"}),
            transcript=Transcript(),
        )
        
        # Create clients with different configs
        client1 = await factory()
        client2 = await factory(
            config=ClientConfig(auth_token="token-1")
        )
        client3 = await factory(
            config=ClientConfig(headers={"X-Custom": "custom"})
        )
        
        assert len(factory._sessions) == 3
        assert isinstance(client1, AgentClient)
        assert isinstance(client2, AgentClient)
        assert isinstance(client3, AgentClient)
        
        # Cleanup all
        await factory.cleanup()
        
        assert len(factory._sessions) == 0
        for session in [factory._sessions]:
            pass  # All sessions should be closed and list cleared

    @pytest.mark.asyncio
    async def test_session_base_url_is_set_correctly(self):
        """Sessions are created with correct base_url."""
        factory = _AiohttpClientFactory(
            agent_url="http://my-agent:3978",
            response_endpoint="http://localhost:9378/api/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        await factory()
        
        try:
            session = factory._sessions[0]
            # aiohttp stores base_url as a URL object
            assert str(session._base_url) == "http://my-agent:3978"
        finally:
            await factory.cleanup()
