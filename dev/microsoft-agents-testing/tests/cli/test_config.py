# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for CLI configuration loading and management."""

import os
import tempfile
from pathlib import Path

import pytest

from microsoft_agents.testing.cli.config import load_environment, CLIConfig


class TestLoadEnvironment:
    """Tests for the load_environment function."""

    def test_returns_empty_dict_when_file_not_found(self):
        """Returns empty dict and None path when env file doesn't exist."""
        env, path = load_environment("nonexistent.env")
        
        assert env == {}
        assert path is None

    def test_loads_variables_from_env_file(self, tmp_path: Path):
        """Successfully loads environment variables from .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\nBAZ=qux\n")
        
        env, path = load_environment(str(env_file))
        
        assert env == {"FOO": "bar", "BAZ": "qux"}
        assert path == str(env_file.resolve())

    def test_handles_empty_env_file(self, tmp_path: Path):
        """Returns empty dict for empty env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("")
        
        env, path = load_environment(str(env_file))
        
        assert env == {}
        assert path == str(env_file.resolve())

    def test_handles_comments_and_empty_lines(self, tmp_path: Path):
        """Ignores comments and empty lines in env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
# This is a comment
KEY1=value1

# Another comment
KEY2=value2
""")
        
        env, path = load_environment(str(env_file))
        
        assert env == {"KEY1": "value1", "KEY2": "value2"}

    def test_handles_quoted_values(self, tmp_path: Path):
        """Properly handles quoted values in env file."""
        env_file = tmp_path / ".env"
        env_file.write_text('QUOTED="hello world"\nSINGLE=\'single quotes\'')
        
        env, path = load_environment(str(env_file))
        
        # dotenv_values strips quotes
        assert env["QUOTED"] == "hello world"
        assert env["SINGLE"] == "single quotes"


class TestCLIConfigInitialization:
    """Tests for CLIConfig class initialization."""

    def test_loads_agent_url_from_env_file(self, tmp_path: Path):
        """CLIConfig loads AGENT_URL from env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("AGENT_URL=http://localhost:3978/api/messages")
        
        config = CLIConfig(str(env_file), "SERVICE_CONNECTION")
        
        assert config.agent_url == "http://localhost:3978/api/messages"

    def test_loads_service_url_from_env_file(self, tmp_path: Path):
        """CLIConfig loads SERVICE_URL from env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("SERVICE_URL=http://localhost:8080")
        
        config = CLIConfig(str(env_file), "SERVICE_CONNECTION")
        
        assert config.service_url == "http://localhost:8080"

    def test_loads_connection_credentials(self, tmp_path: Path):
        """CLIConfig loads credentials for named connection."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
CONNECTIONS__MY_CONN__SETTINGS__CLIENTID=app-id-123
CONNECTIONS__MY_CONN__SETTINGS__CLIENTSECRET=secret-456
CONNECTIONS__MY_CONN__SETTINGS__TENANTID=tenant-789
""")
        
        config = CLIConfig(str(env_file), "MY_CONN")
        
        assert config.app_id == "app-id-123"
        assert config.app_secret == "secret-456"
        assert config.tenant_id == "tenant-789"

    def test_connection_name_is_case_insensitive(self, tmp_path: Path):
        """Connection name matching is case-insensitive."""
        env_file = tmp_path / ".env"
        env_file.write_text("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=my-app-id")
        
        # Pass lowercase connection name
        config = CLIConfig(str(env_file), "service_connection")
        
        assert config.app_id == "my-app-id"

    def test_env_path_property_returns_resolved_path(self, tmp_path: Path):
        """env_path property returns the resolved path to loaded env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value")
        
        config = CLIConfig(str(env_file), "SERVICE_CONNECTION")
        
        assert config.env_path == str(env_file.resolve())

    def test_env_path_is_none_when_file_not_found(self):
        """env_path is None when env file doesn't exist."""
        config = CLIConfig("nonexistent.env", "SERVICE_CONNECTION")
        
        assert config.env_path is None

    def test_env_property_returns_uppercase_keys(self, tmp_path: Path):
        """env property returns dictionary with uppercase keys."""
        env_file = tmp_path / ".env"
        env_file.write_text("lowercase_key=value\nMIXED_Case=other")
        
        config = CLIConfig(str(env_file), "SERVICE_CONNECTION")
        
        assert "LOWERCASE_KEY" in config.env
        assert "MIXED_CASE" in config.env
        # Original case keys should not exist
        assert "lowercase_key" not in config.env
        assert "MIXed_Case" not in config.env

    def test_missing_values_default_to_none(self, tmp_path: Path):
        """Properties default to None when not in env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("")  # Empty file
        
        config = CLIConfig(str(env_file), "SERVICE_CONNECTION")
        
        assert config.app_id is None
        assert config.app_secret is None
        assert config.tenant_id is None
        assert config.agent_url is None
        assert config.service_url is None


class TestCLIConfigIntegration:
    """Integration tests for CLIConfig with realistic configurations."""

    def test_full_configuration_scenario(self, tmp_path: Path):
        """CLIConfig correctly loads a complete configuration."""
        env_file = tmp_path / ".env"
        env_file.write_text("""
# Agent connection settings
AGENT_URL=https://my-agent.azurewebsites.net/api/messages
SERVICE_URL=http://localhost:3979

# Service connection credentials
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=00000000-0000-0000-0000-000000000001
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=super-secret-value
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=00000000-0000-0000-0000-000000000002
""")
        
        config = CLIConfig(str(env_file), "SERVICE_CONNECTION")
        
        assert config.agent_url == "https://my-agent.azurewebsites.net/api/messages"
        assert config.service_url == "http://localhost:3979"
        assert config.app_id == "00000000-0000-0000-0000-000000000001"
        assert config.app_secret == "super-secret-value"
        assert config.tenant_id == "00000000-0000-0000-0000-000000000002"
