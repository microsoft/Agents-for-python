# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Tests for error resources and error message formatting.
"""

import pytest
from microsoft_agents.hosting.core.errors import (
    ErrorMessage,
    ErrorResources,
    error_resources,
)


class TestErrorMessage:
    """Tests for ErrorMessage class."""

    def test_error_message_basic(self):
        """Test basic error message creation."""
        error = ErrorMessage("Test error message", -60000, "test-anchor")
        assert error.message_template == "Test error message"
        assert error.error_code == -60000
        assert error.help_url_anchor == "test-anchor"

    def test_error_message_format_no_args(self):
        """Test formatting error message without arguments."""
        error = ErrorMessage("Simple error", -60001, "test")
        formatted = error.format()
        assert "Simple error" in formatted
        assert "Error Code: -60001" in formatted
        assert "Help URL: https://aka.ms/M365AgentsErrorCodes/#test" in formatted

    def test_error_message_format_with_positional_args(self):
        """Test formatting error message with positional arguments."""
        error = ErrorMessage("Error with {0} and {1}", -60002, "test")
        formatted = error.format("arg1", "arg2")
        assert "Error with arg1 and arg2" in formatted
        assert "Error Code: -60002" in formatted

    def test_error_message_format_with_keyword_args(self):
        """Test formatting error message with keyword arguments."""
        error = ErrorMessage("Error with {name} and {value}", -60003, "test")
        formatted = error.format(name="test_name", value="test_value")
        assert "Error with test_name and test_value" in formatted
        assert "Error Code: -60003" in formatted

    def test_error_message_str(self):
        """Test string representation of error message."""
        error = ErrorMessage("Test error", -60004, "test")
        str_repr = str(error)
        assert "Test error" in str_repr
        assert "Error Code: -60004" in str_repr

    def test_error_message_repr(self):
        """Test repr of error message."""
        error = ErrorMessage("Test error message", -60005, "test")
        repr_str = repr(error)
        assert "ErrorMessage" in repr_str
        assert "-60005" in repr_str


class TestErrorResources:
    """Tests for ErrorResources class."""

    def test_error_resources_singleton(self):
        """Test that error_resources is accessible."""
        assert error_resources is not None
        assert isinstance(error_resources, ErrorResources)

    def test_authentication_errors_exist(self):
        """Test that authentication errors are defined."""
        assert hasattr(error_resources, "FailedToAcquireToken")
        assert hasattr(error_resources, "InvalidInstanceUrl")
        assert hasattr(error_resources, "OnBehalfOfFlowNotSupportedManagedIdentity")

    def test_storage_errors_exist(self):
        """Test that storage errors are defined."""
        assert hasattr(error_resources, "CosmosDbConfigRequired")
        assert hasattr(error_resources, "CosmosDbEndpointRequired")
        assert hasattr(error_resources, "StorageKeyCannotBeEmpty")

    def test_teams_errors_exist(self):
        """Test that teams errors are defined."""
        assert hasattr(error_resources, "TeamsBadRequest")
        assert hasattr(error_resources, "TeamsContextRequired")
        assert hasattr(error_resources, "TeamsMeetingIdRequired")

    def test_hosting_errors_exist(self):
        """Test that hosting errors are defined."""
        assert hasattr(error_resources, "AdapterRequired")
        assert hasattr(error_resources, "AgentApplicationRequired")
        assert hasattr(error_resources, "StreamAlreadyEnded")

    def test_activity_errors_exist(self):
        """Test that activity errors are defined."""
        assert hasattr(error_resources, "InvalidChannelIdType")
        assert hasattr(error_resources, "ChannelIdProductInfoConflict")

    def test_copilot_studio_errors_exist(self):
        """Test that copilot studio errors are defined."""
        assert hasattr(error_resources, "CloudBaseAddressRequired")
        assert hasattr(error_resources, "EnvironmentIdRequired")

    def test_general_errors_exist(self):
        """Test that general errors are defined."""
        assert hasattr(error_resources, "InvalidConfiguration")
        assert hasattr(error_resources, "RequiredParameterMissing")

    def test_error_code_ranges(self):
        """Test that error codes are in expected ranges."""
        # Authentication errors: -60000 to -60099
        assert -60099 <= error_resources.FailedToAcquireToken.error_code <= -60000

        # Storage errors: -60100 to -60199
        assert -60199 <= error_resources.CosmosDbConfigRequired.error_code <= -60100

        # Teams errors: -60200 to -60299
        assert -60299 <= error_resources.TeamsBadRequest.error_code <= -60200

        # Hosting errors: -60300 to -60399
        assert -60399 <= error_resources.AdapterRequired.error_code <= -60300

        # Activity errors: -60400 to -60499
        assert -60499 <= error_resources.InvalidChannelIdType.error_code <= -60400

        # Copilot Studio errors: -60500 to -60599
        assert -60599 <= error_resources.CloudBaseAddressRequired.error_code <= -60500

        # General errors: -60600 to -60699
        assert -60699 <= error_resources.InvalidConfiguration.error_code <= -60600

    def test_failed_to_acquire_token_format(self):
        """Test FailedToAcquireToken error formatting."""
        error = error_resources.FailedToAcquireToken
        formatted = error.format("test_payload")
        assert "Failed to acquire token. test_payload" in formatted
        assert "Error Code: -60012" in formatted
        assert "agentic-identity-with-the-m365-agents-sdk" in formatted

    def test_cosmos_db_config_required(self):
        """Test CosmosDbConfigRequired error formatting."""
        error = error_resources.CosmosDbConfigRequired
        formatted = str(error)
        assert "CosmosDBStorage: CosmosDBConfig is required." in formatted
        assert "Error Code: -60100" in formatted

    def test_teams_context_required(self):
        """Test TeamsContextRequired error formatting."""
        error = error_resources.TeamsContextRequired
        formatted = str(error)
        assert "context is required." in formatted
        assert "Error Code: -60202" in formatted

    def test_error_with_multiple_arguments(self):
        """Test error with multiple format arguments."""
        error = error_resources.CosmosDbPartitionKeyInvalid
        formatted = error.format("key1", "key2")
        assert "key1" in formatted
        assert "key2" in formatted
        assert "Error Code: -60106" in formatted
