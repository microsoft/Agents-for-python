# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Decorator for CLI commands that interact with agents via scenarios.

Provides a unified way to handle both ExternalScenario (external agents)
and AiohttpScenario (in-process agents) in CLI commands.
"""

from __future__ import annotations

from microsoft_agents.testing.core import (
    ExternalScenario,
    Scenario,
    ScenarioConfig,
)
from microsoft_agents.testing.scenario_registry import load_scenarios, scenario_registry

from .cli_context import CLIConfig
from .output import Output

def _resolve_scenario(
    agent_name_or_url: str | None,
    module_path: str | None,
    config: CLIConfig,
    out: Output,
) -> Scenario | None:
    """Create the appropriate scenario based on the provided options.
    """
    
    scenario_config = ScenarioConfig(
        env_file_path=config.env_path,
    )

    if agent_name_or_url:
        if agent_name_or_url.startswith("https://"):   
            out.debug(f"Using external agent at: {agent_name_or_url}")
            return ExternalScenario(agent_name_or_url, config=scenario_config) 
        else:
            if module_path:
                load_scenarios(module_path)
                out.debug(f"Scenarios loaded from module: {module_path}")
            
            try:
                return scenario_registry.get(agent_name_or_url)
            except KeyError as e:
                return None

    return None