# Click CLI Library: A Comprehensive Guide

A concise, breadth-first introduction to Python's [Click library](https://click.palletsprojects.com/) for building robust command-line interfaces.

---

## Table of Contents

1. [Philosophy & Why Click](#1-philosophy--why-click)
2. [Basic Commands](#2-basic-commands)
3. [Options](#3-options)
4. [Arguments](#4-arguments)
5. [Command Groups & Subcommands](#5-command-groups--subcommands)
6. [Context & State Management](#6-context--state-management)
7. [Parameter Types](#7-parameter-types)
8. [User Interaction](#8-user-interaction)
9. [Output & Styling](#9-output--styling)
10. [Error Handling](#10-error-handling)
11. [Environment Variables](#11-environment-variables)
12. [File Handling](#12-file-handling)
13. [Callbacks & Validation](#13-callbacks--validation)
14. [Help & Documentation](#14-help--documentation)
15. [Shell Completion](#15-shell-completion)
16. [Testing](#16-testing)
17. [Advanced Patterns](#17-advanced-patterns)
18. [Packaging & Distribution](#18-packaging--distribution)

---

## 1. Philosophy & Why Click

Click was created to address limitations in `argparse` and `optparse`. Its design principles:

| Principle | Description |
|-----------|-------------|
| **Composability** | Build complex CLIs from simple, reusable pieces |
| **Arbitrary Nesting** | Commands can contain subcommands infinitely deep |
| **Automatic Help** | Help pages generated from docstrings and decorators |
| **Lazy Loading** | Large CLIs don't pay startup cost for unused commands |
| **Context System** | Clean way to pass state between commands |

### Click vs Alternatives

| Feature | Click | argparse | Typer |
|---------|-------|----------|-------|
| Decorator-based | ✅ | ❌ | ✅ |
| Subcommand groups | ✅ Native | Manual | ✅ |
| Type hints | Optional | ❌ | Required |
| Testing utilities | ✅ `CliRunner` | ❌ | ✅ |
| Shell completion | ✅ Built-in | ❌ | ✅ |

---

## 2. Basic Commands

A command is a decorated function. The function name becomes the command name.

```python
import click

@click.command()
def hello():
    """Say hello - this docstring becomes the help text."""
    click.echo("Hello, World!")

if __name__ == "__main__":
    hello()
```

```bash
$ python hello.py
Hello, World!

$ python hello.py --help
Usage: hello.py [OPTIONS]

  Say hello - this docstring becomes the help text.

Options:
  --help  Show this message and exit.
```

### Command Settings

```python
@click.command(
    name="greet",                    # Override command name
    help="Custom help text",         # Override docstring
    epilog="Example: greet --name Bob",  # Text after options
    hidden=True,                     # Hide from help
    deprecated=True,                 # Mark as deprecated
    no_args_is_help=True,           # Show help if no args
)
```

---

## 3. Options

Options are optional parameters with `--name` or `-n` syntax.

### Basic Options

```python
@click.command()
@click.option("--name", default="World", help="Name to greet")
@click.option("--count", "-c", default=1, help="Number of times")
def hello(name, count):
    for _ in range(count):
        click.echo(f"Hello, {name}!")
```

### Option Variants

```python
# Required option
@click.option("--config", required=True)

# Flag (boolean, no value)
@click.option("--verbose", "-v", is_flag=True)

# Counted flag (-vvv = 3)
@click.option("-v", "--verbose", count=True)

# Multiple values (can repeat)
@click.option("--include", "-I", multiple=True)
# Usage: cmd --include foo --include bar

# Fixed number of values
@click.option("--pos", nargs=2, type=float)
# Usage: cmd --pos 1.5 2.5

# Prompt for missing value
@click.option("--password", prompt=True, hide_input=True)

# Confirmation prompt
@click.option("--password", prompt=True, confirmation_prompt=True)

# Show default in help
@click.option("--threads", default=4, show_default=True)

# Hide from help
@click.option("--debug", hidden=True, is_flag=True)
```

### Option Names & Parameter Names

```python
# Short and long form
@click.option("-v", "--verbose")  # Parameter: verbose

# Rename the parameter
@click.option("-n", "--name", "username")  # Parameter: username

# Secondary options (both work)
@click.option("--shout/--no-shout", default=False)
# Usage: cmd --shout or cmd --no-shout
```

### Boolean Flags

```python
# Simple flag
@click.option("--debug", is_flag=True)

# Flag with explicit on/off
@click.option("--color/--no-color", default=True)

# Secondary flag names
@click.option("--verbose", "-v", "--debug", "-d", is_flag=True)
```

---

## 4. Arguments

Arguments are positional, required by default, and ordered.

```python
@click.command()
@click.argument("filename")
@click.argument("destination", required=False)
def copy(filename, destination):
    """Copy FILENAME to DESTINATION."""
    dest = destination or f"{filename}.bak"
    click.echo(f"Copying {filename} to {dest}")
```

### Argument Variants

```python
# Optional argument
@click.argument("output", required=False, default="out.txt")

# Multiple arguments (variadic)
@click.argument("files", nargs=-1)  # Collects all remaining args
# Usage: cmd file1.txt file2.txt file3.txt
# files = ("file1.txt", "file2.txt", "file3.txt")

# Fixed number of arguments
@click.argument("point", nargs=2, type=float)
# Usage: cmd 1.5 2.5
# point = (1.5, 2.5)
```

### Options vs Arguments

| Aspect | Options | Arguments |
|--------|---------|-----------|
| Syntax | `--flag value` | `value` |
| Required | No (by default) | Yes (by default) |
| Order | Any | Fixed |
| Named in help | Shows `--flag` | Shows `NAME` |
| Best for | Configuration | Primary inputs |

---

## 5. Command Groups & Subcommands

Groups create hierarchical CLIs like `git commit`, `docker run`.

```python
@click.group()
def cli():
    """Database management tool."""
    pass

@cli.command()
def init():
    """Initialize the database."""
    click.echo("Database initialized")

@cli.command()
@click.argument("name")
def create(name):
    """Create a new table."""
    click.echo(f"Created table: {name}")

if __name__ == "__main__":
    cli()
```

```bash
$ python db.py --help
Usage: db.py [OPTIONS] COMMAND [ARGS]...

  Database management tool.

Commands:
  create  Create a new table.
  init    Initialize the database.

$ python db.py create users
Created table: users
```

### Group Options

Options on groups are shared by all subcommands:

```python
@click.group()
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

@cli.command()
@click.pass_context
def status(ctx):
    if ctx.obj["verbose"]:
        click.echo("Detailed status...")
    else:
        click.echo("OK")
```

### Dynamic Command Registration

```python
# Method 1: Decorator
@cli.command()
def newcmd():
    pass

# Method 2: add_command()
cli.add_command(some_command)
cli.add_command(other_command, name="alias")

# Method 3: Loop
commands = [cmd1, cmd2, cmd3]
for cmd in commands:
    cli.add_command(cmd)
```

### Nested Groups

```python
@click.group()
def cli():
    pass

@cli.group()
def user():
    """User management commands."""
    pass

@user.command()
def list():
    """List all users."""
    pass

@user.command()
def create():
    """Create a user."""
    pass

# Usage: cli user list, cli user create
```

### Invoke Other Commands

```python
@cli.command()
@click.pass_context
def deploy(ctx):
    """Deploy (runs build first)."""
    ctx.invoke(build)  # Call another command
    click.echo("Deploying...")
```

---

## 6. Context & State Management

The Context object passes state through command hierarchies.

### Basic Context Usage

```python
@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx, debug):
    ctx.ensure_object(dict)  # Initialize ctx.obj if None
    ctx.obj["DEBUG"] = debug

@cli.command()
@click.pass_context
def sync(ctx):
    if ctx.obj["DEBUG"]:
        click.echo("Debug mode is on")
```

### Context Properties

```python
ctx.obj                    # User data (any type, typically dict)
ctx.parent                 # Parent context (from group)
ctx.info_name              # Name of the current command
ctx.params                 # Dict of all parameters
ctx.args                   # Remaining arguments
ctx.invoked_subcommand     # Which subcommand will run (in groups)
ctx.command                # The Command object itself
ctx.color                  # Whether to use ANSI colors
```

### Context Settings

```python
CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"],
    max_content_width=120,
    auto_envvar_prefix="MYAPP",
    default_map={"command": {"option": "value"}},
)

@click.command(context_settings=CONTEXT_SETTINGS)
def cli():
    pass
```

### `@click.pass_obj` Shorthand

If you only need `ctx.obj`:

```python
@cli.command()
@click.pass_obj
def status(obj):
    debug = obj["DEBUG"]
```

### Custom Object Type

```python
class Config:
    def __init__(self):
        self.verbose = False
        self.home = "."

pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option("--verbose", is_flag=True)
@pass_config
def cli(config, verbose):
    config.verbose = verbose

@cli.command()
@pass_config
def sync(config):
    if config.verbose:
        click.echo("Verbose mode")
```

---

## 7. Parameter Types

Click has many built-in types and supports custom types.

### Built-in Types

```python
click.STRING              # Default, any string
click.INT                 # Integer
click.FLOAT               # Float
click.BOOL                # Boolean
click.UUID                # UUID

click.IntRange(0, 100)    # Integer with range validation
click.IntRange(min=0)     # Only minimum
click.IntRange(max=100)   # Only maximum
click.IntRange(0, 100, clamp=True)  # Clamp to range

click.FloatRange(0.0, 1.0)

click.DateTime(formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"])

click.Choice(["json", "xml", "csv"], case_sensitive=False)

click.Path(
    exists=True,          # Must exist
    file_okay=True,       # Can be file
    dir_okay=True,        # Can be directory
    readable=True,        # Must be readable
    writable=True,        # Must be writable
    resolve_path=True,    # Return absolute path
    path_type=Path,       # Return pathlib.Path
)

click.File(
    mode="r",             # File mode
    encoding="utf-8",     # Text encoding
    lazy=True,            # Open on first access
)

click.Tuple([str, int])   # Typed tuple: ("hello", 42)
```

### Custom Types

```python
class URL(click.ParamType):
    name = "url"

    def convert(self, value, param, ctx):
        if not value.startswith(("http://", "https://")):
            self.fail(f"{value!r} is not a valid URL", param, ctx)
        return value

@click.option("--endpoint", type=URL())
```

### Practical Custom Type Example

```python
class CommaSeparated(click.ParamType):
    name = "list"

    def convert(self, value, param, ctx):
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",")]

@click.option("--tags", type=CommaSeparated(), default=[])
# Usage: --tags "foo, bar, baz"
# Result: ["foo", "bar", "baz"]
```

---

## 8. User Interaction

### Prompts

```python
# Basic prompt
name = click.prompt("Your name")

# With default
name = click.prompt("Your name", default="Guest")

# Type conversion
age = click.prompt("Your age", type=int)

# Hidden input (passwords)
password = click.prompt("Password", hide_input=True)

# Confirmation
password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

# Show default in prompt
name = click.prompt("Name", default="Guest", show_default=True)

# Custom prompt suffix
click.prompt("Name", prompt_suffix=": ")
```

### Confirmation

```python
# Simple yes/no
if click.confirm("Do you want to continue?"):
    click.echo("Continuing...")

# Default yes
if click.confirm("Continue?", default=True):
    pass

# Abort on no
click.confirm("This is destructive. Continue?", abort=True)
```

### Launching Editors

```python
# Open default editor
message = click.edit()  # Returns edited text or None

# Edit existing content
message = click.edit("Initial content here")

# Edit specific file
click.edit(filename="config.yaml")

# Specific editor
message = click.edit(editor="vim")
```

### Paging Long Output

```python
# Page through long text (uses less/more)
click.echo_via_pager(very_long_output)

# Generator version (memory efficient)
def generate_lines():
    for i in range(10000):
        yield f"Line {i}\n"

click.echo_via_pager(generate_lines())
```

### Launching Applications

```python
# Open URL in browser
click.launch("https://example.com")

# Open file with default app
click.launch("document.pdf")

# Open file in app, wait for close
click.launch("notes.txt", wait=True)

# Open folder
click.launch("/path/to/folder", locate=True)
```

---

## 9. Output & Styling

### Basic Output

```python
click.echo("Standard output")
click.echo("Error output", err=True)  # To stderr
click.echo()  # Blank line
click.echo("No newline", nl=False)
```

### Styled Output

```python
click.secho("Success!", fg="green")
click.secho("Error!", fg="red", bold=True)
click.secho("Warning", fg="yellow", bg="black")
click.secho("Fancy", underline=True, blink=True)

# Available colors: black, red, green, yellow, blue, magenta, cyan, white, bright_*
# Styles: bold, dim, underline, overline, italic, blink, reverse, strikethrough
```

### Styled Strings (for embedding)

```python
msg = click.style("ERROR", fg="red", bold=True)
click.echo(f"{msg}: Something went wrong")
```

### Progress Bars

```python
# Iterate with progress
with click.progressbar(items, label="Processing") as bar:
    for item in bar:
        process(item)

# Manual progress
with click.progressbar(length=100, label="Downloading") as bar:
    for chunk in download():
        bar.update(len(chunk))

# Customization
with click.progressbar(
    items,
    label="Working",
    show_eta=True,
    show_percent=True,
    show_pos=True,
    width=40,
    fill_char="█",
    empty_char="░",
) as bar:
    for item in bar:
        process(item)
```

### Clear Screen

```python
click.clear()
```

### Get Terminal Size

```python
width, height = click.get_terminal_size()
```

---

## 10. Error Handling

### Exception Types

```python
# Generic exception (exit code 1)
raise click.ClickException("Something went wrong")

# Usage error (shows help hint)
raise click.UsageError("Missing required option")

# Bad parameter (specific parameter)
raise click.BadParameter("Invalid format", param_hint="'--date'")

# Silent abort (exit code 1, no message)
raise click.Abort()

# File error (wraps IOError)
raise click.FileError("config.yaml", hint="File not found")
```

### Exit Codes

```python
# Raise with specific exit code
ctx.exit(2)

# Or via exception
e = click.ClickException("Failed")
e.exit_code = 2
raise e
```

### Graceful Exception Handling

```python
@click.command()
def risky():
    try:
        dangerous_operation()
    except PermissionError:
        raise click.ClickException("Permission denied. Try with sudo.")
    except FileNotFoundError as e:
        raise click.FileError(str(e.filename))
```

### Standalone Mode

When `standalone_mode=False`, exceptions bubble up instead of exiting:

```python
result = cli.main(["arg1", "arg2"], standalone_mode=False)
```

---

## 11. Environment Variables

### Automatic from Option Name

```python
@click.option("--username", envvar="USERNAME")
# Reads from $USERNAME if --username not provided
```

### Multiple Fallbacks

```python
@click.option("--config", envvar=["APP_CONFIG", "CONFIG_FILE"])
# Tries APP_CONFIG first, then CONFIG_FILE
```

### Auto-Prefix

```python
CONTEXT_SETTINGS = {"auto_envvar_prefix": "MYAPP"}

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("--username")  # Reads from MYAPP_USERNAME
@click.option("--password")  # Reads from MYAPP_PASSWORD
def login(username, password):
    pass
```

### Boolean Environment Variables

```python
# These are all truthy: 1, true, yes, on
# These are all falsy: 0, false, no, off, ""

@click.option("--debug", is_flag=True, envvar="DEBUG")
# DEBUG=1 or DEBUG=true enables debug
```

---

## 12. File Handling

### click.File

Opens files automatically, handles `-` as stdin/stdout.

```python
@click.command()
@click.argument("input", type=click.File("r"))
@click.argument("output", type=click.File("w"))
def process(input, output):
    output.write(input.read().upper())
```

```bash
$ echo "hello" | python process.py - output.txt
$ cat input.txt | python process.py - -  # stdin to stdout
```

### Lazy Files

```python
# Opens file only when first accessed
@click.argument("config", type=click.File("r", lazy=True))
```

### Atomic Writes

```python
# Writes to temp file, renames on close (atomic)
@click.argument("output", type=click.File("w", atomic=True))
```

### click.Path

Validates paths without opening them.

```python
@click.option(
    "--config",
    type=click.Path(
        exists=True,
        readable=True,
        path_type=Path,  # Return pathlib.Path
    )
)
def load(config):
    data = config.read_text()  # config is a Path object
```

---

## 13. Callbacks & Validation

### Option Callbacks

Called when option is processed.

```python
def validate_count(ctx, param, value):
    if value < 0:
        raise click.BadParameter("Count must be non-negative")
    return value

@click.option("--count", callback=validate_count, default=1)
```

### Eager Options

Processed before other parameters. Useful for `--version`, `--help`.

```python
def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo("Version 1.0.0")
    ctx.exit()

@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,  # Don't pass to function
    is_eager=True,       # Process first
)
```

### Version Option (Built-in)

```python
@click.command()
@click.version_option(version="1.0.0", prog_name="MyApp")
def cli():
    pass
```

### Value Processing Chain

```python
def normalize_path(ctx, param, value):
    if value:
        return os.path.normpath(value)
    return value

@click.option("--path", callback=normalize_path)
```

---

## 14. Help & Documentation

### Docstring Formatting

```python
@click.command()
def deploy():
    """Deploy the application.
    
    This performs the following steps:
    
    \b
    1. Build the assets
    2. Run database migrations
    3. Restart services
    
    The \\b marker prevents Click from rewrapping the list.
    
    WARNING: This is destructive in production!
    """
```

### Epilog (Text After Options)

```python
@click.command(epilog="See https://example.com for more info")
```

### Custom Help Option

```python
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

@click.command(context_settings=CONTEXT_SETTINGS)
def cli():
    pass
```

### Short Help (for Group Listings)

```python
@click.command(short_help="Deploy the app")
def deploy():
    """This is the full help text that appears when running
    deploy --help. The short_help appears in group listings."""
```

### Rich Markup (Click 8+)

```python
@click.command()
@click.rich_config(help_config={"style": "bold cyan"})
def cli():
    """This is [bold red]styled[/] help text."""
```

### Custom Help Command

```python
class CustomGroup(click.Group):
    def format_help(self, ctx, formatter):
        formatter.write("CUSTOM HEADER\n\n")
        super().format_help(ctx, formatter)

@click.group(cls=CustomGroup)
def cli():
    pass
```

---

## 15. Shell Completion

### Enabling Completion

```bash
# Bash
eval "$(_MYAPP_COMPLETE=bash_source myapp)"

# Zsh
eval "$(_MYAPP_COMPLETE=zsh_source myapp)"

# Fish
_MYAPP_COMPLETE=fish_source myapp | source

# Generate script files (for .bashrc)
_MYAPP_COMPLETE=bash_source myapp > ~/.myapp-complete.bash
echo ". ~/.myapp-complete.bash" >> ~/.bashrc
```

### Custom Completions

```python
def complete_users(ctx, param, incomplete):
    users = ["alice", "bob", "charlie"]
    return [u for u in users if u.startswith(incomplete)]

@click.option("--user", shell_complete=complete_users)
```

### CompletionItem for Rich Completions

```python
from click.shell_completion import CompletionItem

def complete_env(ctx, param, incomplete):
    return [
        CompletionItem("production", help="Production environment"),
        CompletionItem("staging", help="Staging environment"),
        CompletionItem("development", help="Development environment"),
    ]

@click.option("--env", shell_complete=complete_env)
```

### Type-Based Completion

```python
# Path completion is automatic for click.Path
@click.argument("config", type=click.Path())

# Choice completion is automatic
@click.option("--format", type=click.Choice(["json", "yaml", "xml"]))
```

---

## 16. Testing

### CliRunner

```python
from click.testing import CliRunner
from myapp import cli

def test_basic():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    
    assert result.exit_code == 0
    assert "Usage:" in result.output

def test_with_args():
    runner = CliRunner()
    result = runner.invoke(cli, ["create", "--name", "test"])
    
    assert result.exit_code == 0
    assert "Created: test" in result.output
```

### Result Object

```python
result.exit_code      # Exit code
result.output         # stdout as string
result.exception      # Exception if any
result.exc_info       # Exception traceback info
```

### Isolated Filesystem

```python
def test_file_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("input.txt", "w") as f:
            f.write("test data")
        
        result = runner.invoke(cli, ["process", "input.txt"])
        assert result.exit_code == 0
```

### Environment Variables

```python
def test_with_env():
    runner = CliRunner(env={"API_KEY": "secret123"})
    result = runner.invoke(cli, ["auth"])
    assert result.exit_code == 0
```

### Input Simulation

```python
def test_prompt():
    runner = CliRunner()
    result = runner.invoke(cli, ["login"], input="user\npassword\n")
    assert "Welcome, user" in result.output
```

### Catching Exceptions

```python
def test_with_exceptions():
    runner = CliRunner()
    result = runner.invoke(cli, ["fail"], catch_exceptions=False)
    # Raises exception instead of catching it
```

### Mixed stdout/stderr

```python
runner = CliRunner(mix_stderr=False)
result = runner.invoke(cli, ["cmd"])
print(result.output)      # stdout only
print(result.stderr)      # stderr only (requires mix_stderr=False)
```

---

## 17. Advanced Patterns

### Chained Commands

Run multiple commands in sequence, passing results.

```python
@click.group(chain=True)
def cli():
    pass

@cli.command()
def init():
    return {"initialized": True}

@cli.command()
def build():
    return {"built": True}

@cli.result_callback()
def process_results(results):
    """Called with list of all command return values."""
    click.echo(f"Results: {results}")

# Usage: cli init build
# Results: [{"initialized": True}, {"built": True}]
```

### Pipelines with Chained Commands

```python
@click.group(chain=True, invoke_without_command=True)
def cli():
    pass

@cli.result_callback()
def process_pipeline(processors, input):
    for processor in processors:
        input = processor(input)
    return input

@cli.command("upper")
def uppercase():
    return lambda x: x.upper()

@cli.command("reverse")
def reverse():
    return lambda x: x[::-1]
```

### Lazy Loading (Large CLIs)

```python
import importlib

class LazyGroup(click.Group):
    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        return sorted(self.lazy_subcommands.keys())

    def get_command(self, ctx, cmd_name):
        if cmd_name not in self.lazy_subcommands:
            return None
        module_path = self.lazy_subcommands[cmd_name]
        module = importlib.import_module(module_path)
        return module.cli

@click.group(cls=LazyGroup, lazy_subcommands={
    "build": "myapp.commands.build",
    "deploy": "myapp.commands.deploy",
})
def cli():
    pass
```

### Multi-Value Options with Callbacks

```python
def parse_key_value(ctx, param, value):
    result = {}
    for item in value:
        key, val = item.split("=", 1)
        result[key] = val
    return result

@click.option(
    "--set", "-s",
    multiple=True,
    callback=parse_key_value,
    help="Set key=value pairs",
)
def configure(set):
    for key, value in set.items():
        click.echo(f"{key} = {value}")

# Usage: cmd --set name=foo --set count=5
```

### Command Aliases

```python
class AliasedGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        aliases = {
            "ls": "list",
            "rm": "remove",
            "mv": "move",
        }
        cmd_name = aliases.get(cmd_name, cmd_name)
        return super().get_command(ctx, cmd_name)

@click.group(cls=AliasedGroup)
def cli():
    pass
```

### Default Command

```python
class DefaultGroup(click.Group):
    def __init__(self, *args, default_cmd=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_cmd = default_cmd

    def resolve_command(self, ctx, args):
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            if self.default_cmd:
                return self.default_cmd, self.get_command(ctx, self.default_cmd), args
            raise

@click.group(cls=DefaultGroup, default_cmd="status")
def cli():
    pass
```

### Plugins System

```python
import pkg_resources

@click.group()
def cli():
    pass

# Load plugins from entry points
for ep in pkg_resources.iter_entry_points("myapp.plugins"):
    plugin = ep.load()
    cli.add_command(plugin)
```

---

## 18. Packaging & Distribution

### Entry Points (pyproject.toml)

```toml
[project.scripts]
myapp = "myapp.cli:main"

# Or for multiple commands
[project.scripts]
myapp = "myapp.cli:cli"
myapp-admin = "myapp.admin:cli"
```

### Entry Points (setup.py)

```python
setup(
    entry_points={
        "console_scripts": [
            "myapp=myapp.cli:main",
        ],
    },
)
```

### Main Function Pattern

```python
# myapp/cli.py
import click

@click.group()
def cli():
    """MyApp command-line interface."""
    pass

@cli.command()
def version():
    click.echo("1.0.0")

def main():
    cli()

if __name__ == "__main__":
    main()
```

### setuptools Integration

```python
# Use Click's built-in testing instead of unittest.main
from click.testing import CliRunner

def test_cli():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
```

---

## Quick Reference Card

| Feature | Code |
|---------|------|
| Command | `@click.command()` |
| Group | `@click.group()` |
| Option | `@click.option("--name", "-n")` |
| Required | `@click.option("--id", required=True)` |
| Flag | `@click.option("--verbose", is_flag=True)` |
| Count | `@click.option("-v", count=True)` |
| Multiple | `@click.option("--tag", multiple=True)` |
| Choice | `type=click.Choice(["a", "b"])` |
| Range | `type=click.IntRange(0, 100)` |
| Path | `type=click.Path(exists=True)` |
| File | `type=click.File("r")` |
| Argument | `@click.argument("name")` |
| Variadic | `@click.argument("files", nargs=-1)` |
| Context | `@click.pass_context` |
| Object | `@click.pass_obj` |
| Env var | `envvar="VAR"` |
| Callback | `callback=validate_fn` |
| Version | `@click.version_option()` |
| Output | `click.echo()` |
| Styled | `click.secho("msg", fg="green")` |
| Prompt | `click.prompt("Input")` |
| Confirm | `click.confirm("Sure?")` |
| Error | `raise click.ClickException("msg")` |
| Abort | `raise click.Abort()` |
| Progress | `click.progressbar(items)` |

---

## Resources

- [Official Click Documentation](https://click.palletsprojects.com/)
- [Click GitHub Repository](https://github.com/pallets/click)
- [Click 8.0 Changelog](https://click.palletsprojects.com/changes/#version-8-0-0) (major features)
- [Flask CLI](https://flask.palletsprojects.com/cli/) (built on Click)
- [Typer](https://typer.tiangolo.com/) (Click + Type Hints)
