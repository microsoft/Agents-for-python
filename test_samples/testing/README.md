# Testing an AgentApplication

This sample shows how to define one `AgentApplication` and exercise it in two
different environments:

- `python src/app.py` creates the aiohttp
  `CloudAdapter`, and web host.
- `uv run pytest` imports the same module-level application and drives its routes
  entirely in memory with `TestAdapter` and `TestFlow`.

Keeping the hosting setup inside the `if __name__ == "__main__"` block means
that importing `app.py` in a test does not open a port or construct a
production adapter. The test configuration supplies placeholder credentials
for the import-time MSAL connection manager; it never requests a token.

## Project layout

```text
testing/
|-- pyproject.toml
|-- pytest.ini
|-- src/
|   |-- app.py
|   `-- start_server.py
`-- tests/
    |-- conftest.py
    `-- test_app.py
```

`AGENT_APP` and its routes are defined at module scope. The production entry
point creates a `CloudAdapter` only when `src/app.py` is executed directly;
the pytest fixture instead passes `AGENT_APP.on_turn` to `TestFlow`.

## Run the tests

From this directory:

```bash
uv sync
uv run pytest
```

If uv cannot reach PyPI but pip is configured to use an accessible package
index, use the provided requirements file instead:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pytest
```

On Linux or macOS, activate the environment with
`source .venv/bin/activate`.

The tests cover echo, help, conversation-update, and multi-turn behavior. They
assert user-visible outcomes rather than recreating the route implementation.

## Run the aiohttp host

Copy `env.TEMPLATE` to `.env` and replace the placeholder values with the
credentials for your agent registration. Then run:

```bash
uv run python src/app.py
```

The server listens on `http://localhost:3978/api/messages`. Set `PORT` to use a
different port.
