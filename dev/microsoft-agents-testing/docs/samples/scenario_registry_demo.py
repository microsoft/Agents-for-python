#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Scenario Registry — register, discover, and look up named scenarios.

Features demonstrated:
  - scenario_registry.register()  — register a scenario under a name.
  - scenario_registry.get()       — retrieve a scenario by name.
  - scenario_registry.discover()  — glob-pattern discovery across namespaces.
  - Dot-notation namespacing      — organise scenarios as "namespace.name".
  - load_scenarios()              — bulk-register from an importable module.

Run::

    python -m docs.samples.scenario_registry_demo
"""

import asyncio

from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing import (
    AiohttpScenario,
    AgentEnvironment,
    scenario_registry,
)


# ---------------------------------------------------------------------------
# 1) Define a few agents
# ---------------------------------------------------------------------------

async def init_echo(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def h(ctx: TurnContext, state: TurnState):
        await ctx.send_activity(f"Echo: {ctx.activity.text}")


async def init_greeter(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def h(ctx: TurnContext, state: TurnState):
        await ctx.send_activity(f"Hello, {ctx.activity.text}!")


# ---------------------------------------------------------------------------
# 2) Register scenarios in the global registry
# ---------------------------------------------------------------------------

# Names use dot-notation for namespacing
scenario_registry.register(
    "samples.echo",
    AiohttpScenario(init_echo, use_jwt_middleware=False),
    description="Simple echo agent for demos",
)

scenario_registry.register(
    "samples.greeter",
    AiohttpScenario(init_greeter, use_jwt_middleware=False),
    description="Greeter agent that says hello",
)


# ---------------------------------------------------------------------------
# 3) Look up and run scenarios by name
# ---------------------------------------------------------------------------

async def main() -> None:

    # ── get() — retrieve a single scenario by exact name ────────────
    echo = scenario_registry.get("samples.echo")
    async with echo.client() as client:
        replies = await client.send_expect_replies("World")
        print(f"Echo agent replied: {replies[0].text}")

    # ── discover() — find scenarios matching a glob pattern ─────────
    all_samples = scenario_registry.discover("samples.*")
    print(f"\nDiscovered {len(all_samples)} scenario(s) in 'samples' namespace:")
    for name, entry in all_samples.items():
        print(f"  {name:25s}  {entry.description}")

    # ── Iterate all registered scenarios ────────────────────────────
    print(f"\nAll registered scenarios ({len(scenario_registry)}):")
    for entry in scenario_registry:
        print(f"  {entry.name:25s}  namespace={entry.namespace!r}")

    # ── Membership check ────────────────────────────────────────────
    assert "samples.echo" in scenario_registry
    assert "nonexistent" not in scenario_registry

    print("\nScenario registry examples complete.")


if __name__ == "__main__":
    asyncio.run(main())
