from contextlib import contextmanager
from pathlib import Path
import logging
import tempfile
import io

import click
import pytest

from microsoft_agents.testing.cli.cli_config import cli_config

# agents-cli --env_path .\agents\basic_agent\python\.env ddt .\tests\basic_agent\directline\SendActivity_ConversationUpdate_ReturnsWelcomeMessage.yaml --pytest-args -xvs

@contextmanager
def log_context():
# Setup log capture for non-pytest logs
    log_stream = io.StringIO()
    log_handler = logging.StreamHandler(log_stream)
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    
    # Add handler to root logger to capture all logs
    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_handlers = root_logger.handlers.copy()
    
    # Remove all existing handlers to prevent duplicate output
    for handler in original_handlers:
        root_logger.removeHandler(handler)
    
    # Add our capture handler
    root_logger.addHandler(log_handler)

    yield

    # Remove our handler and restore original handlers
    root_logger.removeHandler(log_handler)
    for handler in original_handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(original_level)
    
    # Output captured logs
    log_contents = log_stream.getvalue()
    if log_contents:
        click.echo("\n" + "="*80)
        click.echo("CAPTURED LOGS:")
        click.echo("="*80)
        click.echo(log_contents)
        click.echo("="*80 + "\n")
    
    log_stream.close()

@click.command()
@click.argument("test_path", default="./")
@click.option("--service_url", default="http://localhost:8001/", help='Service URL to reply to')
@click.option("--pytest-args", default="-v -s", help='Arguments to pass to pytest as a string')
@click.pass_context
def ddt(ctx, test_path: str, service_url: str, pytest_args: str):

    env_path = ctx.obj["env_path"]

    test_path = str(Path(test_path).absolute())

    agent_url = cli_config.agent_url

    # Write the test class as actual Python code
    test_code = f'''
from microsoft_agents.testing.integration import ddt as ddt_decorator, Integration

@ddt_decorator(r"{test_path}")
class Test(Integration):
    _agent_url = r"{agent_url}"
    _service_url = r"{service_url}"
    _config_path = r"{env_path}"
'''

    # Create temp file in a known directory to avoid pytest scanning issues
    temp_dir = Path(tempfile.gettempdir()) / "microsoft_agents_cli"
    temp_dir = temp_dir.absolute()
    temp_dir.mkdir(exist_ok=True)
    
    temp_file = temp_dir / f"test_ddt_{Path(test_path).stem}.py"
    temp_file.write_text(test_code)

    with log_context():
        try:
            # Use --override-ini to prevent pytest from using parent configs
            # and --rootdir to set a specific root
            exit_code = pytest.main([
                *pytest_args.split(),
                "--override-ini=testpaths=.",
                "--asyncio-mode=auto",
                f"--rootdir={temp_dir}",
                str(temp_file)
            ])
        finally:
            temp_file.unlink(missing_ok=True)

    return exit_code