# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for CLI main module and command registration."""

from pathlib import Path

import click
from click.testing import CliRunner

from microsoft_agents.testing.cli.main import cli


class TestCLIBasics:
    """Tests for basic CLI functionality."""

    def test_cli_displays_help(self):
        """CLI displays help text when invoked with --help."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "Microsoft Agents Testing CLI" in result.output

    def test_cli_shows_available_commands(self):
        """CLI help shows all registered commands."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["--help"])
        
        # Check that expected commands are listed
        assert "validate" in result.output
        assert "post" in result.output
        assert "chat" in result.output
        assert "run" in result.output

    def test_cli_accepts_env_option(self):
        """CLI accepts --env option for env file path."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["--help"])
        
        assert "--env" in result.output or "-e" in result.output

    def test_cli_accepts_verbose_flag(self):
        """CLI accepts --verbose flag."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["--help"])
        
        assert "--verbose" in result.output or "-v" in result.output

    def test_cli_accepts_connection_option(self):
        """CLI accepts --connection option for named connections."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["--help"])
        
        assert "--connection" in result.output or "-c" in result.output


class TestCLIWithEnvFile:
    """Tests for CLI with environment file handling."""

    def test_cli_uses_default_env_file_when_not_specified(self, tmp_path: Path):
        """CLI uses .env in current directory by default."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create a .env file in the isolated filesystem
            Path(".env").write_text("AGENT_URL=http://test-agent")
            
            result = runner.invoke(cli, ["validate"])
            
            # Should complete successfully and show the agent URL from .env
            assert "http://test-agent" in result.output

    def test_cli_loads_custom_env_file(self, tmp_path: Path):
        """CLI loads environment from custom path when --env is specified."""
        runner = CliRunner()
        env_file = tmp_path / "custom.env"
        env_file.write_text("AGENT_URL=http://custom-agent")
        
        result = runner.invoke(cli, ["--env", str(env_file), "validate"])
        
        assert "http://custom-agent" in result.output

    def test_cli_aborts_when_specified_env_file_not_found(self, tmp_path: Path):
        """CLI aborts with error when specified env file doesn't exist."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["--env", "nonexistent.env", "validate"])
        
        # Should abort (non-zero exit code or aborted output)
        assert result.exit_code != 0 or "Aborted" in result.output


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_shows_configuration_validation_header(self, tmp_path: Path):
        """validate command displays configuration validation header."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".env").write_text("")
            result = runner.invoke(cli, ["validate"])
        
        assert "Configuration Validation" in result.output

    def test_validate_shows_all_config_fields(self, tmp_path: Path):
        """validate command checks all configuration fields."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".env").write_text("")
            result = runner.invoke(cli, ["validate"])
        
        # Should show checks for all fields
        assert "App ID" in result.output
        assert "App Secret" in result.output
        assert "Tenant ID" in result.output
        assert "Agent URL" in result.output
        assert "Service URL" in result.output

    def test_validate_shows_success_for_configured_values(self, tmp_path: Path):
        """validate command shows success for configured values."""
        runner = CliRunner()
        env_file = tmp_path / ".env"
        env_file.write_text("""
AGENT_URL=http://localhost:3978
SERVICE_URL=http://localhost:8080
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=app-id
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=secret
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=tenant-id
""")
        
        result = runner.invoke(cli, ["--env", str(env_file), "validate"])
        
        assert "All configuration checks passed" in result.output

    def test_validate_shows_warnings_for_missing_values(self, tmp_path: Path):
        """validate command shows warnings for missing configuration."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".env").write_text("AGENT_URL=http://test")
            result = runner.invoke(cli, ["validate"])
        
        # Should warn about missing values
        assert "Not configured" in result.output or "missing" in result.output.lower()

    def test_validate_masks_app_id(self, tmp_path: Path):
        """validate command masks sensitive app ID in output."""
        runner = CliRunner()
        env_file = tmp_path / ".env"
        env_file.write_text("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=abcdefghijklmnop")
        
        result = runner.invoke(cli, ["--env", str(env_file), "validate"])
        
        # App ID should be partially masked
        assert "abcdefgh..." in result.output
        # Full ID should NOT appear
        assert "abcdefghijklmnop" not in result.output

    def test_validate_masks_app_secret(self, tmp_path: Path):
        """validate command completely masks app secret."""
        runner = CliRunner()
        env_file = tmp_path / ".env"
        env_file.write_text("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=my-super-secret")
        
        result = runner.invoke(cli, ["--env", str(env_file), "validate"])
        
        # Secret should be masked
        assert "********" in result.output
        # Actual secret should NOT appear
        assert "my-super-secret" not in result.output


class TestPostCommandPayloadLoading:
    """Tests for the post command's payload loading functionality."""

    def test_post_displays_help(self):
        """post command displays help text."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["post", "--help"])
        
        assert result.exit_code == 0
        assert "Send a payload to an agent" in result.output

    def test_post_requires_payload_or_message(self, tmp_path: Path):
        """post command requires either payload file or message."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".env").write_text("AGENT_URL=http://localhost:3978")
            result = runner.invoke(cli, ["post"])
        
        # Should error about missing payload
        assert result.exit_code != 0 or "No payload specified" in result.output


class TestRunCommand:
    """Tests for the run command."""

    def test_run_displays_help(self):
        """run command displays help text."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["run", "--help"])
        
        assert result.exit_code == 0

    def test_run_requires_valid_scenario(self, tmp_path: Path):
        """run command errors on invalid scenario name."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path(".env").write_text("AGENT_URL=http://localhost:3978")
            result = runner.invoke(cli, ["run", "--scenario", "nonexistent"])
        
        # Should error about invalid scenario
        assert result.exit_code != 0 or "Invalid" in result.output or "Aborted" in result.output


class TestChatCommand:
    """Tests for the chat command."""

    def test_chat_displays_help(self):
        """chat command displays help text."""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["chat", "--help"])
        
        assert result.exit_code == 0
        assert "--url" in result.output or "-u" in result.output


class TestVerboseMode:
    """Tests for verbose mode across CLI."""

    def test_verbose_flag_passed_to_context(self, tmp_path: Path):
        """--verbose flag is accessible in command context."""
        runner = CliRunner()
        env_file = tmp_path / ".env"
        env_file.write_text("AGENT_URL=http://localhost")
        
        # Run validate with verbose - should work without error
        result = runner.invoke(cli, ["--verbose", "--env", str(env_file), "validate"])
        
        assert result.exit_code == 0
