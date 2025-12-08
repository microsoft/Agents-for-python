# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Any

from microsoft_agents.testing.cli.common.create_payload_sender import (
    create_payload_sender,
)


class TestCreatePayloadSender:
    """Test suite for create_payload_sender function."""

    @pytest.fixture
    def mock_token(self):
        """Fixture for mocked token."""
        return "mock_bearer_token_12345"

    @pytest.fixture
    def mock_config(self):
        """Fixture for mocked CLI config."""
        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.cli_config"
        ) as mock:
            mock.app_id = "test-app-id"
            mock.app_secret = "test-app-secret"
            mock.tenant_id = "test-tenant-id"
            mock.agent_endpoint = "http://localhost:3978/api/messages/"
            yield mock

    @pytest.fixture
    def sample_payload(self):
        """Fixture for sample payload."""
        return {
            "type": "message",
            "text": "Hello, world!",
            "from": {"id": "user1", "name": "Test User"},
        }

    @pytest.mark.asyncio
    async def test_create_payload_sender_returns_callable(
        self, sample_payload, mock_config, mock_token
    ):
        """Test that create_payload_sender returns a callable."""
        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ):
            sender = create_payload_sender(sample_payload)
            assert callable(sender)

    @pytest.mark.asyncio
    async def test_payload_sender_generates_token_with_correct_params(
        self, sample_payload, mock_config, mock_token
    ):
        """Test that token generation is called with correct parameters."""
        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ) as mock_generate_token:
            create_payload_sender(sample_payload)

            mock_generate_token.assert_called_once_with(
                mock_config.app_id,
                mock_config.app_secret,
                mock_config.tenant_id,
            )

    @pytest.mark.asyncio
    async def test_payload_sender_makes_post_request(
        self, sample_payload, mock_config, mock_token
    ):
        """Test that payload sender makes a POST request with correct parameters."""
        mock_response = Mock()
        mock_response.content = b"Response content"

        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            return_value=mock_response,
        ) as mock_post:
            sender = create_payload_sender(sample_payload)
            result = await sender()

            mock_post.assert_called_once_with(
                mock_config.agent_endpoint,
                headers={
                    "Authorization": f"Bearer {mock_token}",
                    "Content-Type": "application/json",
                },
                json=sample_payload,
                timeout=60,
            )
            assert result == b"Response content"

    @pytest.mark.asyncio
    async def test_payload_sender_with_custom_timeout(
        self, sample_payload, mock_config, mock_token
    ):
        """Test that custom timeout is respected."""
        mock_response = Mock()
        mock_response.content = b"Response content"
        custom_timeout = 120

        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            return_value=mock_response,
        ) as mock_post:
            sender = create_payload_sender(sample_payload, timeout=custom_timeout)
            await sender()

            assert mock_post.call_args[1]["timeout"] == custom_timeout

    @pytest.mark.asyncio
    async def test_payload_sender_returns_response_content(
        self, sample_payload, mock_config, mock_token
    ):
        """Test that payload sender returns response content."""
        expected_content = b'{"status": "success", "id": "123"}'
        mock_response = Mock()
        mock_response.content = expected_content

        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            return_value=mock_response,
        ):
            sender = create_payload_sender(sample_payload)
            result = await sender()

            assert result == expected_content

    @pytest.mark.asyncio
    async def test_payload_sender_uses_asyncio_to_thread(
        self, sample_payload, mock_config, mock_token
    ):
        """Test that the sender uses asyncio.to_thread for the blocking call."""
        mock_response = Mock()
        mock_response.content = b"Response content"

        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            return_value=mock_response,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.asyncio.to_thread",
            new_callable=AsyncMock,
        ) as mock_to_thread:
            mock_to_thread.return_value = mock_response

            sender = create_payload_sender(sample_payload)
            await sender()

            mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_payload_sender_with_empty_payload(
        self, mock_config, mock_token
    ):
        """Test payload sender with an empty payload."""
        empty_payload: dict[str, Any] = {}
        mock_response = Mock()
        mock_response.content = b""

        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            return_value=mock_response,
        ) as mock_post:
            sender = create_payload_sender(empty_payload)
            result = await sender()

            mock_post.assert_called_once()
            assert mock_post.call_args[1]["json"] == empty_payload
            assert result == b""

    @pytest.mark.asyncio
    async def test_payload_sender_with_complex_payload(
        self, mock_config, mock_token
    ):
        """Test payload sender with a complex nested payload."""
        complex_payload = {
            "type": "message",
            "text": "Complex message",
            "attachments": [
                {"contentType": "application/json", "content": {"key": "value"}},
                {"contentType": "text/plain", "content": "Plain text"},
            ],
            "channelData": {"custom": {"nested": {"data": [1, 2, 3]}}},
        }
        mock_response = Mock()
        mock_response.content = b"Response"

        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            return_value=mock_response,
        ) as mock_post:
            sender = create_payload_sender(complex_payload)
            await sender()

            assert mock_post.call_args[1]["json"] == complex_payload

    @pytest.mark.asyncio
    async def test_multiple_invocations_of_same_sender(
        self, sample_payload, mock_config, mock_token
    ):
        """Test that the same sender can be invoked multiple times."""
        mock_response = Mock()
        mock_response.content = b"Response"

        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            return_value=mock_response,
        ) as mock_post:
            sender = create_payload_sender(sample_payload)

            # Call sender multiple times
            await sender()
            await sender()
            await sender()

            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_authorization_header_format(
        self, sample_payload, mock_config, mock_token
    ):
        """Test that the Authorization header is correctly formatted."""
        mock_response = Mock()
        mock_response.content = b"Response"

        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            return_value=mock_response,
        ) as mock_post:
            sender = create_payload_sender(sample_payload)
            await sender()

            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == f"Bearer {mock_token}"
            assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_payload_sender_request_exception_propagates(
        self, sample_payload, mock_config, mock_token
    ):
        """Test that exceptions from requests.post are propagated."""
        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            side_effect=Exception("Network error"),
        ):
            sender = create_payload_sender(sample_payload)

            with pytest.raises(Exception, match="Network error"):
                await sender()

    @pytest.mark.asyncio
    async def test_different_payloads_create_independent_senders(
        self, mock_config, mock_token
    ):
        """Test that different payloads create independent sender functions."""
        payload1 = {"type": "message", "text": "Message 1"}
        payload2 = {"type": "message", "text": "Message 2"}

        mock_response = Mock()
        mock_response.content = b"Response"

        with patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.generate_token",
            return_value=mock_token,
        ), patch(
            "microsoft_agents.testing.cli.common.create_payload_sender.requests.post",
            return_value=mock_response,
        ) as mock_post:
            sender1 = create_payload_sender(payload1)
            sender2 = create_payload_sender(payload2)

            await sender1()
            await sender2()

            assert mock_post.call_count == 2
            # Verify different payloads were sent
            assert mock_post.call_args_list[0][1]["json"] == payload1
            assert mock_post.call_args_list[1][1]["json"] == payload2