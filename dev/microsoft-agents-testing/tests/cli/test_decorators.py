# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for CLI decorators."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import click
from click.testing import CliRunner

from microsoft_agents.testing.cli.core.decorators import async_command
from microsoft_agents.testing.cli.core.with_scenario import (
    with_scenario,
    ScenarioContext,
    _load_agent_module,
    _create_scenario,
)


class TestAsyncCommandDecorator:
    """Tests for the async_command decorator."""

    def test_async_command_runs_coroutine(self):
        """async_command decorator allows async functions as click commands."""
        runner = CliRunner()
        
        @click.command()
        @async_command
        async def my_async_cmd():
            click.echo("async executed")
        
        result = runner.invoke(my_async_cmd)
        
        assert result.exit_code == 0
        assert "async executed" in result.output

    def test_async_command_passes_arguments(self):
        """async_command decorator properly passes arguments to async function."""
        runner = CliRunner()
        
        @click.command()
        @click.argument("name")
        @async_command
        async def greet(name: str):
            click.echo(f"Hello, {name}!")
        
        result = runner.invoke(greet, ["World"])
        
        assert result.exit_code == 0
        assert "Hello, World!" in result.output

    def test_async_command_passes_options(self):
        """async_command decorator properly passes options to async function."""
        runner = CliRunner()
        
        @click.command()
        @click.option("--count", default=1, type=int)
        @async_command
        async def repeat(count: int):
            for i in range(count):
                click.echo(f"Iteration {i + 1}")
        
        result = runner.invoke(repeat, ["--count", "3"])
        
        assert result.exit_code == 0
        assert "Iteration 1" in result.output
        assert "Iteration 2" in result.output
        assert "Iteration 3" in result.output

    def test_async_command_with_context(self):
        """async_command decorator works with click.pass_context."""
        runner = CliRunner()
        
        @click.command()
        @click.pass_context
        @async_command
        async def ctx_cmd(ctx: click.Context):
            ctx.ensure_object(dict)
            ctx.obj["called"] = True
            click.echo("Context accessed")
        
        result = runner.invoke(ctx_cmd)
        
        assert result.exit_code == 0
        assert "Context accessed" in result.output

    def test_async_command_awaits_coroutines(self):
        """async_command properly awaits coroutines."""
        runner = CliRunner()
        results = []
        
        async def async_helper():
            await asyncio.sleep(0.01)  # Small delay to ensure it's async
            return "helper result"
        
        @click.command()
        @async_command
        async def cmd_with_await():
            result = await async_helper()
            click.echo(f"Got: {result}")
        
        result = runner.invoke(cmd_with_await)
        
        assert result.exit_code == 0
        assert "Got: helper result" in result.output

    def test_async_command_propagates_exceptions(self):
        """async_command propagates exceptions from async function."""
        runner = CliRunner()
        
        @click.command()
        @async_command
        async def failing_cmd():
            raise ValueError("Something went wrong")
        
        result = runner.invoke(failing_cmd)
        
        # Exception should propagate, resulting in non-zero exit
        assert result.exit_code != 0
        assert "ValueError" in str(result.exception) or result.exception is not None

    def test_async_command_handles_click_abort(self):
        """async_command handles click.Abort properly."""
        runner = CliRunner()
        
        @click.command()
        @async_command
        async def aborting_cmd():
            raise click.Abort()
        
        result = runner.invoke(aborting_cmd)
        
        # Click Abort should be handled gracefully
        assert "Aborted" in result.output or result.exit_code == 1


class TestWithScenarioDecorator:
    """Tests for the with_scenario decorator."""

    def test_scenario_context_attributes(self):
        """ScenarioContext provides access to scenario, client, config, and verbose."""
        mock_scenario = MagicMock()
        mock_client = MagicMock()
        mock_config = MagicMock()
        
        ctx = ScenarioContext(
            scenario=mock_scenario,
            client=mock_client,
            config=mock_config,
            verbose=True,
        )
        
        assert ctx.scenario is mock_scenario
        assert ctx.client is mock_client
        assert ctx.config is mock_config
        assert ctx.verbose is True

    def test_scenario_context_default_verbose_false(self):
        """ScenarioContext defaults verbose to False."""
        ctx = ScenarioContext(
            scenario=MagicMock(),
            client=MagicMock(),
            config=MagicMock(),
        )
        
        assert ctx.verbose is False

    def test_load_agent_module_success(self):
        """_load_agent_module successfully loads a module with init_agent."""
        mock_out = MagicMock()
        
        # Create a mock module with init_agent
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.init_agent = AsyncMock()
            mock_import.return_value = mock_module
            
            result = _load_agent_module("test.module", mock_out)
            
            assert result is mock_module.init_agent
            mock_import.assert_called_once_with("test.module")

    def test_load_agent_module_import_error(self):
        """_load_agent_module raises Abort on ImportError."""
        mock_out = MagicMock()
        
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            
            try:
                _load_agent_module("nonexistent.module", mock_out)
                assert False, "Should have raised Abort"
            except click.Abort:
                pass
            
            mock_out.error.assert_called()

    def test_load_agent_module_no_init_agent(self):
        """_load_agent_module raises Abort if module lacks init_agent."""
        mock_out = MagicMock()
        
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock(spec=[])  # No init_agent attribute
            mock_import.return_value = mock_module
            
            try:
                _load_agent_module("module.without.init", mock_out)
                assert False, "Should have raised Abort"
            except click.Abort:
                pass
            
            mock_out.error.assert_called()

    def test_create_scenario_with_url(self):
        """_create_scenario creates ExternalScenario when URL is provided."""
        mock_config = MagicMock()
        mock_config.env_path = ".env"
        mock_config.agent_url = None
        mock_out = MagicMock()
        
        scenario = _create_scenario(
            agent_url="http://localhost:3978/api/messages",
            agent_module=None,
            config=mock_config,
            out=mock_out,
        )
        
        from microsoft_agents.testing.core import ExternalScenario
        assert isinstance(scenario, ExternalScenario)

    def test_create_scenario_with_config_url(self):
        """_create_scenario uses config.agent_url if no URL is provided."""
        mock_config = MagicMock()
        mock_config.env_path = ".env"
        mock_config.agent_url = "http://configured-agent:3978/api/messages"
        mock_out = MagicMock()
        
        scenario = _create_scenario(
            agent_url=None,
            agent_module=None,
            config=mock_config,
            out=mock_out,
        )
        
        from microsoft_agents.testing.core import ExternalScenario
        assert isinstance(scenario, ExternalScenario)

    def test_create_scenario_no_agent_aborts(self):
        """_create_scenario raises Abort if no agent is specified."""
        mock_config = MagicMock()
        mock_config.env_path = ".env"
        mock_config.agent_url = None
        mock_out = MagicMock()
        
        try:
            _create_scenario(
                agent_url=None,
                agent_module=None,
                config=mock_config,
                out=mock_out,
            )
            assert False, "Should have raised Abort"
        except click.Abort:
            pass
        
        mock_out.error.assert_called()

    def test_create_scenario_agent_module_priority(self):
        """_create_scenario prioritizes --agent over --url."""
        mock_config = MagicMock()
        mock_config.env_path = ".env"
        mock_config.agent_url = "http://external:3978"
        mock_out = MagicMock()
        
        with patch(
            "microsoft_agents.testing.cli.core.with_scenario._load_agent_module"
        ) as mock_load:
            mock_load.return_value = AsyncMock()
            
            scenario = _create_scenario(
                agent_url="http://localhost:3978",
                agent_module="test.module",
                config=mock_config,
                out=mock_out,
            )
            
            from microsoft_agents.testing import AiohttpScenario
            assert isinstance(scenario, AiohttpScenario)
            mock_load.assert_called_once_with("test.module", mock_out)
