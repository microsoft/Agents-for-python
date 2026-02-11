# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Reusable output formatting utilities for CLI commands."""

from typing import Any, Iterator, Optional
from contextlib import contextmanager
import click

from microsoft_agents.activity import Activity


class Output:
    """Helper class for consistent CLI output formatting.
    
    Provides styled output methods and table formatting utilities.
    
    Example:
        >>> out = Output()
        >>> out.success("Operation completed!")
        >>> out.error("Something went wrong")
        >>> out.table(headers=["Name", "Value"], rows=[["foo", "bar"]])
    """
    
    def __init__(self, verbose: bool = False):
        """Initialize the output helper.
        
        Args:
            verbose: Whether to show verbose output.
        """
        self.verbose = verbose

    def header(self, text: str) -> None:
        """Display a section header."""
        click.echo()
        click.secho(text, bold=True)
        click.echo("-" * len(text))

    def success(self, message: str) -> None:
        """Display a success message in green."""
        click.secho(f"✓ {message}", fg="green")

    def error(self, message: str) -> None:
        """Display an error message in red."""
        click.secho(f"✗ {message}", fg="red", err=True)

    def warning(self, message: str) -> None:
        """Display a warning message in yellow."""
        click.secho(f"⚠ {message}", fg="yellow")

    def info(self, message: str) -> None:
        """Display an info message."""
        click.echo(f"  {message}")

    def debug(self, message: str) -> None:
        """Display a debug message (only in verbose mode)."""
        if self.verbose:
            click.secho(f"  [debug] {message}", fg="cyan")

    def newline(self, n: int = 1) -> None:
        """Print a newline for spacing."""
        for _ in range(n):
            click.echo()

    def key_value(self, key: str, value: Any) -> None:
        """Display a key-value pair."""
        click.echo(f"  {click.style(key + ':', bold=True)} {value}")

    def table(
        self, 
        headers: list[str], 
        rows: list[list[Any]],
        col_widths: Optional[list[int]] = None,
    ) -> None:
        """Display a simple ASCII table.
        
        Args:
            headers: Column header names.
            rows: List of row data (each row is a list of values).
            col_widths: Optional list of column widths.
        """
        if col_widths is None:
            # Calculate column widths from content
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Add padding
        col_widths = [w + 2 for w in col_widths]
        
        # Header row
        header_row = "".join(
            str(h).ljust(col_widths[i]) for i, h in enumerate(headers)
        )
        click.secho(header_row, bold=True)
        click.echo("-" * sum(col_widths))
        
        # Data rows
        for row in rows:
            row_str = "".join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
            )
            click.echo(row_str)

    def json(self, data: Any) -> None:
        """Display data as formatted JSON."""
        import json
        click.echo(json.dumps(data, indent=2, default=str))

    def activity(self, activity: Activity) -> None:
        """Display an activity object as formatted JSON."""
        self.json(activity.model_dump_json(exclude_unset=True, exclude_none=True, indent=2))

    def divider(self) -> None:
        """Display a horizontal divider."""
        click.echo("-" * 80)

    def prompt(self) -> str:
        """Prompt the user for input."""
        return click.prompt(">> ")
    
    @contextmanager
    def text_loading(self, message: str) -> Iterator[None]:
        """Context manager for displaying a loading message."""
        click.echo(f"{message}...", nl=False)
        yield
        click.echo("OK")


# Convenience functions for quick access
def success(message: str) -> None:
    """Display a success message."""
    Output().success(message)


def error(message: str) -> None:
    """Display an error message."""
    Output().error(message)


def warning(message: str) -> None:
    """Display a warning message."""
    Output().warning(message)
