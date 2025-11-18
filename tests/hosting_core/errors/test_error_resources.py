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
        error = ErrorMessage("Test error message", -60000)
        assert error.message_template == "Test error message"
        assert error.error_code == -60000

    def test_error_message_format_no_args(self):
        """Test formatting error message without arguments."""
        error = ErrorMessage("Simple error", -60001)
        formatted = error.format()
        assert "Simple error" in formatted
        assert "Error Code: -60001" in formatted
        assert "Help URL: https://aka.ms/M365AgentsErrorCodes/#-60001" in formatted

    def test_error_message_format_with_positional_args(self):
        """Test formatting error message with positional arguments."""
        error = ErrorMessage("Error with {0} and {1}", -60002)
        formatted = error.format("arg1", "arg2")
        assert "Error with arg1 and arg2" in formatted
        assert "Error Code: -60002" in formatted

    def test_error_message_format_with_keyword_args(self):
        """Test formatting error message with keyword arguments."""
        error = ErrorMessage("Error with {name} and {value}", -60003)
        formatted = error.format(name="test_name", value="test_value")
        assert "Error with test_name and test_value" in formatted
        assert "Error Code: -60003" in formatted

    def test_error_message_str(self):
        """Test string representation of error message."""
        error = ErrorMessage("Test error", -60004)
        str_repr = str(error)
        assert "Test error" in str_repr
        assert "Error Code: -60004" in str_repr

    def test_error_message_repr(self):
        """Test repr of error message."""
        error = ErrorMessage("Test error message", -60005)
        repr_str = repr(error)
        assert "ErrorMessage" in repr_str
        assert "-60005" in repr_str


class TestErrorResources:
    """Tests for ErrorResources class (hosting and general errors)."""

    def test_error_resources_singleton(self):
        """Test that error_resources is accessible."""
        assert error_resources is not None
        assert isinstance(error_resources, ErrorResources)

    def test_hosting_errors_exist(self):
        """Test that hosting errors are defined in hosting-core."""
        assert hasattr(error_resources, "AdapterRequired")
        assert hasattr(error_resources, "AgentApplicationRequired")
        assert hasattr(error_resources, "StreamAlreadyEnded")
        assert hasattr(error_resources, "RequestRequired")
        assert hasattr(error_resources, "AgentRequired")

    def test_general_errors_exist(self):
        """Test that general errors are defined in hosting-core."""
        assert hasattr(error_resources, "InvalidConfiguration")
        assert hasattr(error_resources, "RequiredParameterMissing")
        assert hasattr(error_resources, "InvalidParameterValue")

    def test_hosting_error_code_ranges(self):
        """Test that hosting error codes are in expected range."""
        # Hosting errors: -63000 to -63999
        assert -63999 <= error_resources.AdapterRequired.error_code <= -63000
        assert -63999 <= error_resources.StreamAlreadyEnded.error_code <= -63000

    def test_general_error_code_ranges(self):
        """Test that general error codes are in expected range."""
        # General errors: -66000 to -66999
        assert -66999 <= error_resources.InvalidConfiguration.error_code <= -66000
        assert -66999 <= error_resources.RequiredParameterMissing.error_code <= -66000

    def test_adapter_required_format(self):
        """Test AdapterRequired error formatting."""
        error = error_resources.AdapterRequired
        formatted = str(error)
        assert "adapter can't be None" in formatted
        assert "Error Code: -63000" in formatted

    def test_invalid_configuration_format(self):
        """Test InvalidConfiguration error formatting."""
        error = error_resources.InvalidConfiguration
        formatted = error.format("test config error")
        assert "Invalid configuration: test config error" in formatted
        assert "Error Code: -66000" in formatted


class TestDistributedErrorResources:
    """Tests for error resources distributed across packages."""

    def test_authentication_errors_exist(self):
        """Test that authentication errors are defined in their package."""
        try:
            from microsoft_agents.authentication.msal.errors import (
                authentication_errors,
            )

            assert hasattr(authentication_errors, "FailedToAcquireToken")
            assert hasattr(authentication_errors, "InvalidInstanceUrl")
            assert hasattr(
                authentication_errors, "OnBehalfOfFlowNotSupportedManagedIdentity"
            )
            # Test error code range: -60000 to -60999
            assert (
                -60999
                <= authentication_errors.FailedToAcquireToken.error_code
                <= -60000
            )
        except ImportError:
            pytest.skip("Authentication package not available")

    def test_storage_cosmos_errors_exist(self):
        """Test that storage cosmos errors are defined in their package."""
        try:
            from microsoft_agents.storage.cosmos.errors import storage_errors

            assert hasattr(storage_errors, "CosmosDbConfigRequired")
            assert hasattr(storage_errors, "CosmosDbEndpointRequired")
            assert hasattr(storage_errors, "CosmosDbKeyCannotBeEmpty")
            # Test error code range: -61000 to -61999
            assert -61999 <= storage_errors.CosmosDbConfigRequired.error_code <= -61000
        except ImportError:
            pytest.skip("Storage Cosmos package not available")

    def test_storage_blob_errors_exist(self):
        """Test that storage blob errors are defined in their package."""
        try:
            from microsoft_agents.storage.blob.errors import blob_storage_errors

            assert hasattr(blob_storage_errors, "BlobStorageConfigRequired")
            assert hasattr(blob_storage_errors, "BlobContainerNameRequired")
            # Test error code range: -61100 to -61199
            assert (
                -61199
                <= blob_storage_errors.BlobStorageConfigRequired.error_code
                <= -61100
            )
        except ImportError:
            pytest.skip("Storage Blob package not available")

    def test_teams_errors_exist(self):
        """Test that teams errors are defined in their package."""
        try:
            from microsoft_agents.hosting.teams.errors import teams_errors

            assert hasattr(teams_errors, "TeamsBadRequest")
            assert hasattr(teams_errors, "TeamsContextRequired")
            assert hasattr(teams_errors, "TeamsMeetingIdRequired")
            # Test error code range: -62000 to -62999
            assert -62999 <= teams_errors.TeamsBadRequest.error_code <= -62000
        except ImportError:
            pytest.skip("Teams package not available")

    def test_activity_errors_exist(self):
        """Test that activity errors are defined in their package."""
        try:
            from microsoft_agents.activity.errors import activity_errors

            assert hasattr(activity_errors, "InvalidChannelIdType")
            assert hasattr(activity_errors, "ChannelIdProductInfoConflict")
            assert hasattr(activity_errors, "ChannelIdValueConflict")
            # Test error code range: -64000 to -64999
            assert -64999 <= activity_errors.InvalidChannelIdType.error_code <= -64000
        except ImportError:
            pytest.skip("Activity package not available")

    def test_copilot_studio_errors_exist(self):
        """Test that copilot studio errors are defined in their package."""
        try:
            from microsoft_agents.copilotstudio.client.errors import (
                copilot_studio_errors,
            )

            assert hasattr(copilot_studio_errors, "CloudBaseAddressRequired")
            assert hasattr(copilot_studio_errors, "EnvironmentIdRequired")
            assert hasattr(copilot_studio_errors, "AgentIdentifierRequired")
            # Test error code range: -65000 to -65999
            assert (
                -65999
                <= copilot_studio_errors.CloudBaseAddressRequired.error_code
                <= -65000
            )
        except ImportError:
            pytest.skip("Copilot Studio package not available")

    def test_authentication_error_format(self):
        """Test authentication error formatting."""
        try:
            from microsoft_agents.authentication.msal.errors import (
                authentication_errors,
            )

            error = authentication_errors.FailedToAcquireToken
            formatted = error.format("test_payload")
            assert "Failed to acquire token. test_payload" in formatted
            assert "Error Code: -60012" in formatted
            assert "#-60012" in formatted
        except ImportError:
            pytest.skip("Authentication package not available")

    def test_storage_error_format(self):
        """Test storage error formatting."""
        try:
            from microsoft_agents.storage.cosmos.errors import storage_errors

            error = storage_errors.CosmosDbConfigRequired
            formatted = str(error)
            assert "CosmosDBStorage: CosmosDBConfig is required." in formatted
            assert "Error Code: -61000" in formatted
        except ImportError:
            pytest.skip("Storage Cosmos package not available")

    def test_teams_error_format(self):
        """Test teams error formatting."""
        try:
            from microsoft_agents.hosting.teams.errors import teams_errors

            error = teams_errors.TeamsContextRequired
            formatted = str(error)
            assert "context is required." in formatted
            assert "Error Code: -62002" in formatted
        except ImportError:
            pytest.skip("Teams package not available")
