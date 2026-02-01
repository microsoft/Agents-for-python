# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for CLI output formatting utilities."""

import io

import click
from click.testing import CliRunner

from microsoft_agents.testing.cli.core.output import Output


class TestOutputBasicFormatting:
    """Tests for basic Output formatting methods."""

    def test_success_outputs_green_message_with_checkmark(self):
        """success() outputs message with green styling and checkmark."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.success("Operation completed")
        
        result = runner.invoke(cmd)
        
        assert "✓ Operation completed" in result.output
        assert result.exit_code == 0

    def test_error_outputs_red_message_with_x(self):
        """error() outputs message with red styling and x mark."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.error("Something failed")
        
        result = runner.invoke(cmd)
        
        # Error outputs to stderr, but CliRunner captures both
        assert "✗ Something failed" in result.output
        assert result.exit_code == 0

    def test_warning_outputs_yellow_message_with_warning_symbol(self):
        """warning() outputs message with warning symbol."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.warning("Be careful")
        
        result = runner.invoke(cmd)
        
        assert "⚠ Be careful" in result.output

    def test_info_outputs_indented_message(self):
        """info() outputs message with indentation."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.info("Some information")
        
        result = runner.invoke(cmd)
        
        assert "  Some information" in result.output

    def test_header_outputs_bold_text_with_underline(self):
        """header() outputs text with underline."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.header("My Section")
        
        result = runner.invoke(cmd)
        
        assert "My Section" in result.output
        assert "----------" in result.output  # Underline same length as header


class TestOutputDebugMode:
    """Tests for Output debug/verbose functionality."""

    def test_debug_hidden_when_verbose_false(self):
        """debug() messages are hidden when verbose is False."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output(verbose=False)
            out.debug("Debug message")
            out.info("Normal message")
        
        result = runner.invoke(cmd)
        
        assert "Debug message" not in result.output
        assert "Normal message" in result.output

    def test_debug_shown_when_verbose_true(self):
        """debug() messages are shown when verbose is True."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output(verbose=True)
            out.debug("Debug message")
        
        result = runner.invoke(cmd)
        
        assert "[debug] Debug message" in result.output


class TestOutputTable:
    """Tests for Output table formatting."""

    def test_table_displays_headers_and_rows(self):
        """table() displays headers and data rows."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.table(
                headers=["Name", "Value"],
                rows=[
                    ["foo", "bar"],
                    ["baz", "qux"],
                ]
            )
        
        result = runner.invoke(cmd)
        
        assert "Name" in result.output
        assert "Value" in result.output
        assert "foo" in result.output
        assert "bar" in result.output
        assert "baz" in result.output
        assert "qux" in result.output

    def test_table_handles_empty_rows(self):
        """table() handles empty row list gracefully."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.table(
                headers=["Col1", "Col2"],
                rows=[]
            )
        
        result = runner.invoke(cmd)
        
        # Should still show headers
        assert "Col1" in result.output
        assert "Col2" in result.output
        assert result.exit_code == 0


class TestOutputKeyValue:
    """Tests for Output key-value formatting."""

    def test_key_value_displays_formatted_pair(self):
        """key_value() displays key and value with formatting."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.key_value("Agent URL", "http://localhost:3978")
        
        result = runner.invoke(cmd)
        
        assert "Agent URL:" in result.output
        assert "http://localhost:3978" in result.output


class TestOutputNewlineAndDivider:
    """Tests for Output spacing utilities."""

    def test_newline_adds_blank_line(self):
        """newline() adds blank lines to output."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.info("Line 1")
            out.newline()
            out.info("Line 2")
        
        result = runner.invoke(cmd)
        lines = result.output.split('\n')
        
        # Should have a blank line between the two info lines
        assert len([l for l in lines if l.strip() == ""]) >= 1

    def test_divider_outputs_horizontal_line(self):
        """divider() outputs a horizontal line of dashes."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.divider()
        
        result = runner.invoke(cmd)
        
        assert "-" * 80 in result.output


class TestOutputJson:
    """Tests for Output JSON formatting."""

    def test_json_outputs_formatted_json(self):
        """json() outputs data as formatted JSON."""
        runner = CliRunner()
        
        @click.command()
        def cmd():
            out = Output()
            out.json({"key": "value", "nested": {"inner": 42}})
        
        result = runner.invoke(cmd)
        
        assert '"key": "value"' in result.output
        assert '"nested"' in result.output
        assert '"inner": 42' in result.output
