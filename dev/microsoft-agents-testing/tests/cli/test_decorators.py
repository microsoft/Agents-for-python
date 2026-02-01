# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for CLI decorators."""

import asyncio

import click
from click.testing import CliRunner

from microsoft_agents.testing.cli.core.decorators import async_command


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
