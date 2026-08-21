# CLI

The `agt` command is the terminal interface for the testing package. Use it for
quick manual checks, interactive chats, one-off posts, simple load tests, and
scaffolding test harnesses.

```bash
agt [--env FILE] [--connection NAME] [--verbose] COMMAND
```

| Global option | Default | Description |
|---------------|---------|-------------|
| `--env / -e FILE` | `.env` | Environment file to load |
| `--connection / -c NAME` | `SERVICE_CONNECTION` | Named connection for auth credentials |
| `--verbose / -v` | `False` | Print debug output |

## Choosing an agent target

Scenario commands use one of two target options:

| Option | Description |
|--------|-------------|
| `--url / -u URL` | Connect to an agent already running at an HTTP endpoint |
| `--agent / -a NAME` | Use a scenario registered in `scenario_registry` |

Use `--module MODULE` with scenario commands when the scenario registration
lives in another module and must be imported before lookup.

```bash
agt scenario chat --url http://localhost:3978/api/messages
agt scenario chat --agent agt.basic
agt scenario chat --module my_tests.scenarios --agent local.echo
```

## Environment commands

```bash
agt env show
agt env help
```

`env show` prints the Python/runtime context, loaded environment file, loaded
environment variable names, and registered scenario count. `env help` prints the
expected authentication-related `.env` variable names.

## Scenario commands

### List registered scenarios

```bash
agt scenario list
agt scenario list "agt.*"
```

The optional pattern uses the same glob-style matching as
`scenario_registry.discover()`.

### Interactive chat

```bash
agt scenario chat --url http://localhost:3978/api/messages
agt scenario chat --agent agt.basic
```

Starts a REPL-style session. Type `/exit` or `/quit` to end the chat.

### Post one activity

```bash
agt scenario post --url http://localhost:3978/api/messages --message "Hello!"
agt scenario post --url http://localhost:3978/api/messages --json-file activity.json
```

`post` sends one text message or JSON activity and prints the resulting
transcript. Use `--timeout / -t` to control how long to wait for responses, in
milliseconds.

### Load test

```bash
agt scenario load --url http://localhost:3978/api/messages \
    --message "Hello!" --num 50 --timeout 5000

agt scenario load --url http://localhost:3978/api/messages \
    --json_file activity.json --num 20
```

`load` sends the same message or activity concurrently and prints per-request
failures plus aggregate latency statistics. Use either `--message` or
`--json_file`, not both.

### Run an in-process scenario

```bash
agt scenario run --agent agt.basic
```

`run` starts an in-process scenario as a long-running local server. It is not
available for `ExternalScenario` targets because those agents are already
running.

## Scaffolding

```bash
agt init
agt init basic
agt init basic --force
```

Omit the preset name to list available presets. Provide a preset name to copy
that harness into the current directory. `--force` overwrites conflicting files
from the preset.

