# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the AiohttpClientFactory class."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from contextlib import asynccontextmanager

from aiohttp import ClientSession

from microsoft_agents.activity import Activity, ActivityTypes

from microsoft_agents.testing.core.aiohttp_client_factory import AiohttpClientFactory
from microsoft_agents.testing.core.client_config import ClientConfig
from microsoft_agents.testing.core.agent_client import AgentClient
from microsoft_agents.testing.core.fluent import ActivityTemplate
from microsoft_agents.testing.core.transport import Transcript, Exchange


# ============================================================================
# AiohttpClientFactory Initialization Tests
# ============================================================================

class TestAiohttpClientFactoryInitialization:
    """Tests for AiohttpClientFactory initialization."""

    def test_stores_agent_url(self):
        """Factory stores the agent URL."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        assert factory._agent_url == "http://localhost:3978"

    def test_stores_response_endpoint(self):
        """Factory stores the response endpoint."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/v3/conversations/",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        assert factory._response_endpoint == "http://localhost:9378/v3/conversations/"

    def test_stores_sdk_config(self):
        """Factory stores the SDK config."""
        sdk_config = {"CLIENT_ID": "test-id", "CLIENT_SECRET": "test-secret"}
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config=sdk_config,
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        assert factory._sdk_config == sdk_config

    def test_stores_default_template(self):
        """Factory stores the default template."""
        template = ActivityTemplate(channel_id="test-channel")
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=template,
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        assert factory._default_template is template

    def test_stores_default_config(self):
        """Factory stores the default client config."""
        config = ClientConfig(user_id="default-user")
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=config,
            transcript=Transcript(),
        )
        
        assert factory._default_config is config

    def test_stores_transcript(self):
        """Factory stores the transcript."""
        transcript = Transcript()
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=transcript,
        )
        
        assert factory._transcript is transcript

    def test_initializes_empty_sessions_list(self):
        """Factory initializes with empty sessions list."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        assert factory._sessions == []


# ============================================================================
# AiohttpClientFactory Create Client Tests
# ============================================================================

class TestAiohttpClientFactoryCreateClient:
    """Tests for AiohttpClientFactory.create_client() method."""

    @pytest.mark.asyncio
    async def test_create_client_returns_agent_client(self):
        """create_client returns an AgentClient instance."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            client = await factory.create_client()
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_tracks_session(self):
        """create_client adds session to sessions list."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            await factory.create_client()
            assert len(factory._sessions) == 1
            assert isinstance(factory._sessions[0], ClientSession)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_multiple_clients_tracks_all_sessions(self):
        """create_client tracks all created sessions."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            await factory.create_client()
            await factory.create_client()
            await factory.create_client()
            
            assert len(factory._sessions) == 3
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_uses_default_config_when_none(self):
        """create_client uses default config when None provided."""
        default_config = ClientConfig(user_id="default-user", user_name="Default User")
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=default_config,
            transcript=Transcript(),
        )
        
        try:
            client = await factory.create_client(config=None)
            # Client should be created successfully with defaults
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_create_client_uses_provided_config(self):
        """create_client uses provided config over defaults."""
        default_config = ClientConfig(user_id="default-user")
        custom_config = ClientConfig(user_id="custom-user", user_name="Custom User")
        
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=default_config,
            transcript=Transcript(),
        )
        
        try:
            client = await factory.create_client(config=custom_config)
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()


# ============================================================================
# AiohttpClientFactory Headers Tests
# ============================================================================

class TestAiohttpClientFactoryHeaders:
    """Tests for header handling in AiohttpClientFactory."""

    @pytest.mark.asyncio
    async def test_sets_content_type_header(self):
        """create_client sets Content-Type header."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            await factory.create_client()
            session = factory._sessions[0]
            # Session should have Content-Type in headers
            assert "Content-Type" in session.headers or "content-type" in session.headers
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_uses_auth_token_from_config(self):
        """create_client uses auth token from config."""
        config = ClientConfig(auth_token="test-bearer-token")
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            await factory.create_client(config=config)
            session = factory._sessions[0]
            auth_header = session.headers.get("Authorization", "")
            assert "Bearer test-bearer-token" in auth_header
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_merges_custom_headers(self):
        """create_client merges custom headers from config."""
        config = ClientConfig(headers={"X-Custom-Header": "custom-value"})
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            await factory.create_client(config=config)
            session = factory._sessions[0]
            assert session.headers.get("X-Custom-Header") == "custom-value"
        finally:
            await factory.cleanup()


# ============================================================================
# AiohttpClientFactory Cleanup Tests
# ============================================================================

class TestAiohttpClientFactoryCleanup:
    """Tests for AiohttpClientFactory.cleanup() method."""

    @pytest.mark.asyncio
    async def test_cleanup_closes_all_sessions(self):
        """cleanup closes all created sessions."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        await factory.create_client()
        await factory.create_client()
        
        sessions = list(factory._sessions)  # Copy list before cleanup
        assert len(sessions) == 2
        
        await factory.cleanup()
        
        # All sessions should be closed
        for session in sessions:
            assert session.closed

    @pytest.mark.asyncio
    async def test_cleanup_clears_sessions_list(self):
        """cleanup clears the sessions list."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        await factory.create_client()
        await factory.create_client()
        
        assert len(factory._sessions) == 2
        
        await factory.cleanup()
        
        assert factory._sessions == []

    @pytest.mark.asyncio
    async def test_cleanup_with_no_sessions(self):
        """cleanup works with no sessions created."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
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
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        await factory.create_client()
        
        await factory.cleanup()
        await factory.cleanup()  # Second call should not raise
        
        assert factory._sessions == []


# ============================================================================
# AiohttpClientFactory Transcript Sharing Tests
# ============================================================================

class TestAiohttpClientFactoryTranscriptSharing:
    """Tests for transcript sharing between clients."""

    @pytest.mark.asyncio
    async def test_all_clients_share_transcript(self):
        """All clients created by factory share the same transcript."""
        transcript = Transcript()
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=transcript,
        )
        
        try:
            client1 = await factory.create_client()
            client2 = await factory.create_client()
            
            # Both should reference the same transcript
            assert client1._transcript is transcript
            assert client2._transcript is transcript
        finally:
            await factory.cleanup()


# ============================================================================
# AiohttpClientFactory Template Handling Tests
# ============================================================================

class TestAiohttpClientFactoryTemplateHandling:
    """Tests for activity template handling."""

    @pytest.mark.asyncio
    async def test_uses_default_template_when_config_has_none(self):
        """Uses default template when config has no template."""
        default_template = ActivityTemplate(channel_id="default-channel")
        config = ClientConfig()  # No template
        
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=default_template,
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            client = await factory.create_client(config=config)
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_uses_config_template_when_provided(self):
        """Uses config template over default when provided."""
        default_template = ActivityTemplate(channel_id="default-channel")
        config_template = ActivityTemplate(channel_id="config-channel")
        config = ClientConfig(activity_template=config_template)
        
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=default_template,
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            client = await factory.create_client(config=config)
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()


# ============================================================================
# AiohttpClientFactory User Identity Tests
# ============================================================================

class TestAiohttpClientFactoryUserIdentity:
    """Tests for user identity handling in factory."""

    @pytest.mark.asyncio
    async def test_creates_client_with_default_user(self):
        """Factory creates client with default user identity."""
        default_config = ClientConfig(user_id="default-user", user_name="Default User")
        
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=default_config,
            transcript=Transcript(),
        )
        
        try:
            client = await factory.create_client()
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_creates_client_with_custom_user(self):
        """Factory creates client with custom user identity."""
        custom_config = ClientConfig(user_id="alice", user_name="Alice")
        
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            client = await factory.create_client(config=custom_config)
            assert isinstance(client, AgentClient)
        finally:
            await factory.cleanup()

    @pytest.mark.asyncio
    async def test_different_clients_can_have_different_users(self):
        """Different clients can be created with different user identities."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            alice = await factory.create_client(
                config=ClientConfig(user_id="alice", user_name="Alice")
            )
            bob = await factory.create_client(
                config=ClientConfig(user_id="bob", user_name="Bob")
            )
            
            assert isinstance(alice, AgentClient)
            assert isinstance(bob, AgentClient)
            assert alice is not bob
        finally:
            await factory.cleanup()


# ============================================================================
# AiohttpClientFactory Protocol Compliance Tests
# ============================================================================

class TestAiohttpClientFactoryProtocolCompliance:
    """Tests for ClientFactory protocol compliance."""

    def test_has_create_client_method(self):
        """AiohttpClientFactory has create_client method."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        assert hasattr(factory, 'create_client')
        assert callable(factory.create_client)

    def test_has_cleanup_method(self):
        """AiohttpClientFactory has cleanup method."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        assert hasattr(factory, 'cleanup')
        assert callable(factory.cleanup)

    @pytest.mark.asyncio
    async def test_create_client_accepts_optional_config(self):
        """create_client accepts optional config parameter."""
        factory = AiohttpClientFactory(
            agent_url="http://localhost:3978",
            response_endpoint="http://localhost:9378/callback",
            sdk_config={},
            default_template=ActivityTemplate(),
            default_config=ClientConfig(),
            transcript=Transcript(),
        )
        
        try:
            # Should work with no config
            client1 = await factory.create_client()
            assert isinstance(client1, AgentClient)
            
            # Should work with config
            client2 = await factory.create_client(config=ClientConfig())
            assert isinstance(client2, AgentClient)
            
            # Should work with None
            client3 = await factory.create_client(None)
            assert isinstance(client3, AgentClient)
        finally:
            await factory.cleanup()
