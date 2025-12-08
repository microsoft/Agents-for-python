# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import pytest
from unittest.mock import patch

from microsoft_agents.testing.cli.cli_config import _CLIConfig, cli_config


class TestCLIConfig:

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = _CLIConfig()
        assert config.tenant_id == ""
        assert config.app_id == ""
        assert config.app_secret == ""
        assert config.agent_url == "http://localhost:3978/"
        assert config.service_url == "http://localhost:8001/"

    def test_agent_endpoint_property(self):
        """Test that agent_endpoint returns the correct URL."""
        config = _CLIConfig()
        assert config.agent_endpoint == "http://localhost:3978/api/messages/"

    def test_agent_endpoint_with_custom_url(self):
        """Test agent_endpoint with a custom agent_url."""
        config = _CLIConfig()
        config.agent_url = "http://example.com:5000/"
        assert config.agent_endpoint == "http://example.com:5000/api/messages/"

    def test_agent_endpoint_without_trailing_slash(self):
        """Test agent_endpoint when agent_url doesn't have trailing slash."""
        config = _CLIConfig()
        config.agent_url = "http://example.com:5000"
        assert config.agent_endpoint == "http://example.com:5000/api/messages/"

    def test_load_from_config_empty_dict(self):
        """Test load_from_config with an empty dictionary."""
        config = _CLIConfig()
        config.load_from_config({})
        
        assert config.tenant_id == ""
        assert config.app_id == ""
        assert config.app_secret == ""
        assert config.agent_url == "http://localhost:3978/"

    def test_load_from_config_partial_dict(self):
        """Test load_from_config with partial configuration."""
        config = _CLIConfig()
        config.load_from_config({
            "tenant_id": "test-tenant",
            "app_id": "test-app"
        })
        
        assert config.tenant_id == "test-tenant"
        assert config.app_id == "test-app"
        assert config.app_secret == ""
        assert config.agent_url == "http://localhost:3978/"

    def test_load_from_config_full_dict(self):
        """Test load_from_config with full configuration."""
        config = _CLIConfig()
        config.load_from_config({
            "tenant_id": "test-tenant",
            "app_id": "test-app",
            "app_secret": "test-secret",
            "agent_url": "http://example.com/"
        })
        
        assert config.tenant_id == "test-tenant"
        assert config.app_id == "test-app"
        assert config.app_secret == "test-secret"
        assert config.agent_url == "http://example.com/"

    def test_load_from_config_none_uses_env(self):
        """Test load_from_config with None uses environment variables."""
        with patch.dict(os.environ, {
            "tenant_id": "env-tenant",
            "app_id": "env-app",
            "app_secret": "env-secret",
            "agent_url": "http://env.example.com/"
        }, clear=False):
            config = _CLIConfig()
            config.load_from_config(None)
            
            assert config.tenant_id == "env-tenant"
            assert config.app_id == "env-app"
            assert config.app_secret == "env-secret"
            assert config.agent_url == "http://env.example.com/"

    def test_load_from_config_updates_existing_values(self):
        """Test that load_from_config updates existing values."""
        config = _CLIConfig()
        config.tenant_id = "old-tenant"
        config.app_id = "old-app"
        
        config.load_from_config({
            "tenant_id": "new-tenant",
            "app_secret": "new-secret"
        })
        
        assert config.tenant_id == "new-tenant"
        assert config.app_id == "old-app"
        assert config.app_secret == "new-secret"

    def test_load_from_connection_default_connection_name(self):
        """Test load_from_connection with default connection name."""
        with patch.dict(os.environ, {
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "connection-app-id",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET": "connection-secret",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "connection-tenant"
        }, clear=False):
            config = _CLIConfig()
            config.load_from_connection()
            
            assert config.app_id == "connection-app-id"
            assert config.app_secret == "connection-secret"
            assert config.tenant_id == "connection-tenant"

    def test_load_from_connection_custom_connection_name(self):
        """Test load_from_connection with custom connection name."""
        with patch.dict(os.environ, {
            "CONNECTIONS__CUSTOM_CONNECTION__SETTINGS__CLIENTID": "custom-app-id",
            "CONNECTIONS__CUSTOM_CONNECTION__SETTINGS__CLIENTSECRET": "custom-secret",
            "CONNECTIONS__CUSTOM_CONNECTION__SETTINGS__TENANTID": "custom-tenant"
        }, clear=False):
            config = _CLIConfig()
            config.load_from_connection("CUSTOM_CONNECTION")
            
            assert config.app_id == "custom-app-id"
            assert config.app_secret == "custom-secret"
            assert config.tenant_id == "custom-tenant"

    def test_load_from_connection_partial_env_vars(self):
        """Test load_from_connection with only some environment variables set."""
        with patch.dict(os.environ, {
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "partial-app-id"
        }, clear=False):
            config = _CLIConfig()
            config.app_secret = "existing-secret"
            config.load_from_connection()
            
            assert config.app_id == "partial-app-id"
            assert config.app_secret == "existing-secret"
            assert config.tenant_id == ""

    def test_load_from_connection_no_env_vars(self):
        """Test load_from_connection with no matching environment variables."""
        config = _CLIConfig()
        config.tenant_id = "existing-tenant"
        config.app_id = "existing-app"
        
        # Ensure no connection env vars exist
        env_clean = {k: v for k, v in os.environ.items() 
                     if not k.startswith("CONNECTIONS__TEST_CONNECTION__")}
        
        with patch.dict(os.environ, env_clean, clear=True):
            config.load_from_connection("TEST_CONNECTION")
            
            # Should retain existing values
            assert config.tenant_id == "existing-tenant"
            assert config.app_id == "existing-app"

    def test_load_from_connection_config_param_unused(self):
        """Test that config parameter in load_from_connection is unused."""
        with patch.dict(os.environ, {
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "env-app-id"
        }, clear=False):
            config = _CLIConfig()
            # The config parameter is defined but not used in the implementation
            config.load_from_connection("SERVICE_CONNECTION", {"app_id": "ignored"})
            
            assert config.app_id == "env-app-id"

    def test_cli_config_singleton_loaded_from_env(self):
        """Test that the module-level cli_config instance is initialized."""
        # The cli_config singleton should be loaded from config on import
        assert isinstance(cli_config, _CLIConfig)


class TestCLIConfigIntegration:
    """Integration tests for _CLIConfig with various scenarios."""

    def test_full_workflow_load_config_then_connection(self):
        """Test loading from config first, then from connection."""
        config = _CLIConfig()
        
        # First load from config
        config.load_from_config({
            "tenant_id": "config-tenant",
            "app_id": "config-app",
            "agent_url": "http://config.example.com/"
        })
        
        assert config.tenant_id == "config-tenant"
        assert config.app_id == "config-app"
        
        # Then load from connection (should override)
        with patch.dict(os.environ, {
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "connection-app",
            "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "connection-tenant"
        }, clear=False):
            config.load_from_connection()
            
            assert config.tenant_id == "connection-tenant"
            assert config.app_id == "connection-app"
            # agent_url should remain from config load
            assert config.agent_url == "http://config.example.com/"

    def test_environment_variable_override(self):
        """Test that environment variables work as expected."""
        prev_env = os.environ.copy()
        os.environ["tenant_id"] = "env-tenant"
        os.environ["app_id"] = "env-app"
        
        config = _CLIConfig()
        config.load_from_config()
        
        assert config.tenant_id == "env-tenant"
        assert config.app_id == "env-app"

        for key in prev_env:
            os.environ[key] = prev_env[key]
