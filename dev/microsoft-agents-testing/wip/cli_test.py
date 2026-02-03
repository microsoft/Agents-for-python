import subprocess
import sys
from pathlib import Path

import click

from ..core import Output


@click.command()
@click.option(
    "--junit-xml", "-j",
    type=click.Path(),
    help="Output JUnit XML report to this file.",
)
@click.option(
    "--html",
    type=click.Path(),
    help="Output HTML report to this file (requires pytest-html).",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose pytest output.",
)
@click.option(
    "--filter", "-k",
    help="Only run tests matching this expression.",
)
@click.argument(
    "path",
    default=".",
    type=click.Path(exists=True),
)
@click.pass_context
def test(ctx: click.Context, junit_xml: str | None, html: str | None, 
         verbose: bool, filter: str | None, path: str) -> None:
    """Run agent tests using pytest.
    
    This command wraps pytest with agent-testing defaults and
    provides convenient options for CI integration.
    
    Examples:
    
        agt test                           # Run all tests in current directory
        agt test tests/                    # Run tests in specific directory
        agt test -j results.xml            # Output JUnit XML for CI
        agt test -k "booking"              # Run only tests matching "booking"
    """
    out = Output(verbose=ctx.obj.get("verbose", False))
    
    # Build pytest command
    pytest_args = [sys.executable, "-m", "pytest"]
    
    # Add path
    pytest_args.append(path)
    
    # Add JUnit XML output
    if junit_xml:
        pytest_args.extend(["--junit-xml", junit_xml])
        out.info(f"JUnit XML output: {junit_xml}")
    
    # Add HTML report
    if html:
        pytest_args.extend(["--html", html, "--self-contained-html"])
        out.info(f"HTML report: {html}")
    
    # Add verbosity
    if verbose:
        pytest_args.append("-v")
    
    # Add filter
    if filter:
        pytest_args.extend(["-k", filter])
    
    out.info(f"Running: {' '.join(pytest_args)}")
    
    # Run pytest
    result = subprocess.run(pytest_args, cwd=Path.cwd())
    
    # Exit with pytest's exit code
    sys.exit(result.returncode)