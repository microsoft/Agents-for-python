# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""CLI scenario resolution utilities.

Provides helper functions for resolving which Scenario to use based
on user-provided CLI options (URL, registered name, or module path).
"""

from __future__ import annotations

from microsoft_agents.testing.core import (
    ExternalScenario,
    Scenario,
    ScenarioConfig,
)
from microsoft_agents.testing.scenario_registry import load_scenarios, scenario_registry

from .cli_config import CLIConfig
from .output import Output

def _resolve_scenario(
    agent_name_or_url: str | None,
    module_path: str | None,
    config: CLIConfig,
    out: Output,
) -> Scenario | None:
    """Resolve a Scenario from user-provided CLI options.

    Checks whether the input is an HTTPS URL (creates ExternalScenario)
    or a registered scenario name (looks up in the registry). If a
    module_path is provided, it is imported first to trigger registration.

    :param agent_name_or_url: A URL or registered scenario name.
    :param module_path: Optional Python module path to import for registration.
    :param config: The CLI configuration.
    :param out: Output helper for debug messages.
    :return: A resolved Scenario, or None if resolution fails.
    """
    
    scenario_config = ScenarioConfig(
        env_file_path=config.env_path,
    )

    if agent_name_or_url:
        # BUG: Only URLs starting with "https://" are detected as external
        # endpoints. Plain "http://" URLs (e.g., http://localhost:3978/...)
        # fall through to the registry lookup and will fail to resolve.
        if agent_name_or_url.startswith("https://") or agent_name_or_url.startswith("http://"):   
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