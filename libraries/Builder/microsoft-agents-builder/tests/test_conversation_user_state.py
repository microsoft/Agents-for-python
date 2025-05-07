"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from microsoft.agents.builder.state.user_state import UserState
from microsoft.agents.builder.app.state.conversation_state import ConversationState
from microsoft.agents.builder.state.agent_state import CachedAgentState
from microsoft.agents.builder.turn_context import TurnContext
from microsoft.agents.storage import Storage
from microsoft.agents.core.models import Activity, ConversationAccount, ChannelAccount


class TestUserState:
    """Tests for the UserState class."""

    def test_initialization(self):
        """Test initialization of UserState."""
        storage = MagicMock(spec=Storage)
        user_state = UserState(storage)

        assert user_state._storage == storage
        assert user_state._context_service_key == "UserState"

    def test_get_storage_key(self):
        """Test getting the storage key."""
        storage = MagicMock(spec=Storage)
        user_state = UserState(storage)

        # Create a mock turn context with user and channel info
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity = Activity(
            channel_id="test-channel", from_property=ChannelAccount(id="user-id")
        )

        # Get the storage key
        key = user_state.get_storage_key(turn_context)

        assert key == "UserState/test-channel/users/user-id"


class TestConversationState:
    """Tests for the ConversationState class."""

    def test_initialization(self):
        """Test initialization of ConversationState."""
        storage = MagicMock(spec=Storage)
        conversation_state = ConversationState(storage)

        assert conversation_state._storage == storage
        assert conversation_state._context_service_key == "ConversationState"

    def test_get_storage_key(self):
        """Test getting the storage key."""
        storage = MagicMock(spec=Storage)
        conversation_state = ConversationState(storage)

        # Create a mock turn context with conversation info
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity = Activity(
            channel_id="test-channel",
            conversation=ConversationAccount(id="conversation-id"),
        )

        # Get the storage key
        key = conversation_state.get_storage_key(turn_context)

        assert key == "ConversationState/test-channel/conversations/conversation-id"


class TestStateIntegration:
    """Integration tests for UserState and ConversationState."""

    @pytest.mark.asyncio
    async def test_user_state_load_and_save(self):
        """Test loading and saving user state."""
        storage = MagicMock(spec=Storage)
        user_state = UserState(storage)

        # Create a mock turn context with user and channel info
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity = Activity(
            channel_id="test-channel", from_property=ChannelAccount(id="user-id")
        )

        # Mock cached state
        cached_state = CachedAgentState()

        # Mock storage read to return some data
        storage_key = "UserState/test-channel/users/user-id"
        storage_data = {
            storage_key: {
                "user_name": "Test User",
                "preferences": {"theme": "dark"},
                "CachedAgentState._hash": 12345,
            }
        }
        storage.read = AsyncMock(return_value=storage_data)
        storage.write = AsyncMock()

        # Make get_cached_state return our mock
        with patch.object(user_state, "get_cached_state", return_value=cached_state):
            # Load state
            await user_state.load(turn_context)

            # Should have read from storage
            storage.read.assert_called_once_with([storage_key])

            # State should be populated with storage data
            assert cached_state.state["user_name"] == "Test User"
            assert cached_state.state["preferences"] == {"theme": "dark"}

            # Modify state
            cached_state.state["user_name"] = "Updated User"

            # Save state
            await user_state.save_changes(turn_context)

            # Should have written to storage
            storage.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_conversation_state_load_and_save(self):
        """Test loading and saving conversation state."""
        storage = MagicMock(spec=Storage)
        conversation_state = ConversationState(storage)

        # Create a mock turn context with conversation info
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity = Activity(
            channel_id="test-channel",
            conversation=ConversationAccount(id="conversation-id"),
        )

        # Mock cached state
        cached_state = CachedAgentState()

        # Mock storage read to return some data
        storage_key = "ConversationState/test-channel/conversations/conversation-id"
        storage_data = {
            storage_key: {
                "conversation_name": "Test Conversation",
                "participants": ["user1", "user2"],
                "CachedAgentState._hash": 12345,
            }
        }
        storage.read = AsyncMock(return_value=storage_data)
        storage.write = AsyncMock()

        # Make get_cached_state return our mock
        with patch.object(
            conversation_state, "get_cached_state", return_value=cached_state
        ):
            # Load state
            await conversation_state.load(turn_context)

            # Should have read from storage
            storage.read.assert_called_once_with([storage_key])

            # State should be populated with storage data
            assert cached_state.state["conversation_name"] == "Test Conversation"
            assert cached_state.state["participants"] == ["user1", "user2"]

            # Modify state
            cached_state.state["participants"].append("user3")

            # Save state
            await conversation_state.save_changes(turn_context)

            # Should have written to storage
            storage.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_and_conversation_state_independence(self):
        """Test that user and conversation states are independent."""
        storage = MagicMock(spec=Storage)
        user_state = UserState(storage)
        conversation_state = ConversationState(storage)

        # Create a mock turn context with both user and conversation info
        turn_context = MagicMock(spec=TurnContext)
        turn_context.activity = Activity(
            channel_id="test-channel",
            from_property=ChannelAccount(id="user-id"),
            conversation=ConversationAccount(id="conversation-id"),
        )

        # Mock cached states
        user_cached_state = CachedAgentState()
        conversation_cached_state = CachedAgentState()

        # Mock storage read to return different data for each state
        user_storage_key = "UserState/test-channel/users/user-id"
        conversation_storage_key = (
            "ConversationState/test-channel/conversations/conversation-id"
        )

        # Create storage data
        storage_data = {
            user_storage_key: {
                "user_name": "Test User",
                "CachedAgentState._hash": 12345,
            },
            conversation_storage_key: {
                "conversation_name": "Test Conversation",
                "CachedAgentState._hash": 67890,
            },
        }

        # Setup mocks
        storage.read = AsyncMock(
            side_effect=lambda keys: {
                k: storage_data[k] for k in keys if k in storage_data
            }
        )

        # Make get_cached_state return our mocks
        with patch.object(
            user_state, "get_cached_state", return_value=user_cached_state
        ):
            with patch.object(
                conversation_state,
                "get_cached_state",
                return_value=conversation_cached_state,
            ):
                # Load both states
                await user_state.load(turn_context)
                await conversation_state.load(turn_context)

                # Verify user state
                assert user_cached_state.state["user_name"] == "Test User"
                assert "conversation_name" not in user_cached_state.state

                # Verify conversation state
                assert (
                    conversation_cached_state.state["conversation_name"]
                    == "Test Conversation"
                )
                assert "user_name" not in conversation_cached_state.state
