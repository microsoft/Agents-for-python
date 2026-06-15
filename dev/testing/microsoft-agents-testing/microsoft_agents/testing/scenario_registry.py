# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Global registry for named test scenarios.

Provides a simple way to register, discover, and retrieve scenarios by name
with optional namespace grouping using dot notation.

Example:
    from microsoft_agents.testing import scenario_registry, ExternalScenario
    
    # Register scenarios
    scenario_registry.register(
        "prod.echo",
        ExternalScenario(url="https://prod.example.com/api/messages"),
        description="Production echo agent",
    )
    
    # Retrieve by name
    scenario = scenario_registry.get("prod.echo")
    
    # List scenarios in a namespace
    prod_scenarios = scenario_registry.discover("prod")
"""

from __future__ import annotations

import sys
import importlib
import json
from pathlib import Path
from fnmatch import fnmatch
from dataclasses import dataclass
from collections.abc import Iterator

from .core import Scenario, ExternalScenario
from .source_scenario import SourceScenario

@dataclass(frozen=True)
class ScenarioEntry:
    """Metadata for a registered scenario.

    Attributes:
        name: The unique registered name for this scenario.
        scenario: The Scenario instance.
        description: Human-readable description of the scenario.
    """

    name: str
    scenario: Scenario
    description: str = ""

    @property
    def namespace(self) -> str:
        """Extract the namespace portion of the scenario name.

        For a name like 'prod.echo', returns 'prod'.
        Returns an empty string if there is no namespace.
        """

        index = self.name.rfind(".")
        if index == -1:
            return ""
        return self.name[:index]

class ScenarioRegistry:
    """Global registry for named test scenarios.
    
    Scenarios are registered by name and can be organized into namespaces
    using dot notation (e.g., "prod.echo", "staging.echo").
    """
    
    def __init__(self) -> None:
        self._entries: dict[str, ScenarioEntry] = {}
    
    def register(
        self,
        name: str,
        scenario: Scenario,
        *,
        description: str = "",
    ) -> None:
        """Register a scenario by name.
        
        Args:
            name: Unique name for the scenario. Use dot notation for namespacing
                  (e.g., "prod.echo", "local.multi-turn").
            scenario: The Scenario instance to register.
            description: Optional human-readable description.
        
        Raises:
            ValueError: If a scenario with this name is already registered.
        
        Example:
            scenario_registry.register(
                "prod.echo",
                ExternalScenario(url="https://prod.example.com"),
                description="Production echo agent test",
            )
        """
        if name in self._entries:
            raise ValueError(f"Scenario '{name}' is already registered")
        if not isinstance(scenario, Scenario):
            raise TypeError("scenario must be an instance of Scenario")
        
        self._entries[name] = ScenarioEntry(
            name=name,
            scenario=scenario,
            description=description,
        )

    def load_json(self, file_path: str) -> None:
        """Load scenarios from a JSON file."""

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        agent_defs = data.get("agents", {})

        for name, body in agent_defs.items():

            path_str = body.get("path", "")
            desc = body.get("description", "")
            script = body.get("script", "")

            if path_str.startswith(("http://", "https://")):
                self.register(
                    name,
                    ExternalScenario(path_str),
                    description=desc,
                )
            else:

                if not script:
                    raise ValueError("A 'script' field is required for source scenarios")

                path = (Path(file_path).resolve().parent / path_str).resolve()
                if not path.exists():
                    raise FileNotFoundError(f"Agent path not found: {path}")
                self.register(
                    name,
                    SourceScenario(path, script),
                    description=desc,
                )

    def get_entry(self, name: str) -> ScenarioEntry:
        """Get the full entry (scenario + metadata) by name."""
        if name not in self._entries:
            available = ", ".join(sorted(self._entries.keys())) or "(none)"
            raise KeyError(f"Scenario '{name}' not found. Available: {available}")
        return self._entries[name]
    
    def get(self, name: str) -> Scenario:
        """Get a scenario by name.
        
        Args:
            name: The registered name of the scenario.
        
        Returns:
            The registered Scenario instance.
        
        Raises:
            KeyError: If no scenario is registered with this name.
        
        Example:
            scenario = scenario_registry.get("prod.echo")
            async with scenario.client() as client:
                replies = await client.send_expect_replies("Hello")
        """
        return self.get_entry(name).scenario
    
    def discover(self, pattern: str = "*") -> dict[str, ScenarioEntry]:
        """Discover scenarios matching a pattern.
        
        Args:
            pattern: Glob-style pattern to match scenario names.
                     Use "*" for all scenarios, "prod.*" for a namespace,
                     or "*.echo" for all echo scenarios across namespaces.
        
        Returns:
            Dictionary of matching scenario names to their entries.
        
        Example:
            # All scenarios
            all_scenarios = scenario_registry.discover()
            
            # All in 'prod' namespace
            prod_scenarios = scenario_registry.discover("prod.*")
            
            # All echo scenarios
            echo_scenarios = scenario_registry.discover("*.echo")
        """
        return {
            name: entry
            for name, entry in self._entries.items()
            if fnmatch(name, pattern)
        }
    
    def __iter__(self) -> Iterator[ScenarioEntry]:
        """Iterate over registered scenario entries."""
        return iter(self._entries.values())
        
    def __contains__(self, name: str) -> bool:
        """Check if a scenario is registered."""
        return name in self._entries
    
    def __len__(self) -> int:
        """Get the number of registered scenarios."""
        return len(self._entries)
    
    def clear(self) -> None:
        """Remove all registered scenarios. Primarily for testing."""
        self._entries.clear()

# Global singlet
# on instance
scenario_registry = ScenarioRegistry()


def _import_modules(module_path: str) -> None:
    """Import a module to trigger scenario registration side-effects.

    Supports both Python module paths (e.g., 'myproject.scenarios')
    and file paths (e.g., './scenarios.py').

    :param module_path: Python module path or file path to import.
    :raises FileNotFoundError: If a file path is provided and does not exist.
    """
    
    if module_path.endswith(".py") or "/" in module_path or "\\" in module_path:
        # File path - load as module
        path = Path(module_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Scenario file not found: {path}")
        
        # Add parent to sys.path temporarily
        parent = str(path.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)
        
        module_name = path.stem
        importlib.import_module(module_name)
        sys.path = [p for p in sys.path if p != parent]
    else:
        # Module path - import directly
        importlib.import_module(module_path)
    

def load_scenarios(module_path: str) -> int:
    """Load scenarios from the specified module or file path.

    Imports the module, which is expected to register scenarios as a
    side-effect. Returns the number of newly registered scenarios.

    :param module_path: Python module path or file path to import.
    :return: Number of scenarios registered during this call.
    """
    before_count = len(scenario_registry)
    try:
        _import_modules(module_path)
    except Exception as e:
        print(f"Error loading scenarios from {module_path}: {e}")

    after_count = len(scenario_registry)

    return after_count - before_count

def resolve_scenario(scenario_or_str: Scenario | str ) -> Scenario:
    """Resolve a scenario from a Scenario instance or a registered name.
    
    If a string is provided, looks up the scenario in the registry.
    
    :param scenario_or_str: A Scenario instance or a string key for lookup.
    :return: The resolved Scenario instance.
    :raises ValueError: If the string key is not found in the registry.
    """
    if isinstance(scenario_or_str, Scenario):
        return scenario_or_str
    elif isinstance(scenario_or_str, str):
        if scenario_or_str.startswith("http://") or scenario_or_str.startswith("https://"):
            # If it's a URL, create an ExternalScenario on the fly
            return ExternalScenario(scenario_or_str)
        else:
            return scenario_registry.get(scenario_or_str)
    else:
        raise TypeError("Input must be a Scenario instance or a string key.")
