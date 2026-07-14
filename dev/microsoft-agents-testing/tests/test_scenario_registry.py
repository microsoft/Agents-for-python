# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for the scenario_registry module."""

import sys
import tempfile
import pytest
from pathlib import Path

from microsoft_agents.testing.scenario_registry import (
    ScenarioEntry,
    ScenarioRegistry,
    scenario_registry,
    load_scenarios,
)
from microsoft_agents.testing.core import ExternalScenario


# ============================================================================
# ScenarioEntry Tests
# ============================================================================

class TestScenarioEntry:
    """Tests for ScenarioEntry dataclass."""

    def test_entry_creation_with_all_fields(self):
        """ScenarioEntry can be created with all fields."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        entry = ScenarioEntry(
            name="test.echo",
            scenario=scenario,
            description="Test echo scenario",
        )

        assert entry.name == "test.echo"
        assert entry.scenario is scenario
        assert entry.description == "Test echo scenario"

    def test_entry_creation_with_default_description(self):
        """ScenarioEntry uses empty string for default description."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        entry = ScenarioEntry(name="test.echo", scenario=scenario)

        assert entry.description == ""

    def test_entry_is_frozen(self):
        """ScenarioEntry is immutable (frozen dataclass)."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        entry = ScenarioEntry(name="test.echo", scenario=scenario)

        with pytest.raises(AttributeError):
            entry.name = "new.name"

    def test_namespace_property_with_dot_notation(self):
        """ScenarioEntry.namespace returns the namespace part of the name."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        entry = ScenarioEntry(name="prod.echo", scenario=scenario)

        assert entry.namespace == "prod"

    def test_namespace_property_with_nested_namespace(self):
        """ScenarioEntry.namespace handles nested namespaces."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        entry = ScenarioEntry(name="prod.us.east.echo", scenario=scenario)

        assert entry.namespace == "prod.us.east"

    def test_namespace_property_without_namespace(self):
        """ScenarioEntry.namespace returns empty string for names without namespace."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        entry = ScenarioEntry(name="echo", scenario=scenario)

        assert entry.namespace == ""


# ============================================================================
# ScenarioRegistry Tests
# ============================================================================

class TestScenarioRegistry:
    """Tests for ScenarioRegistry class."""

    def test_empty_registry_has_zero_length(self):
        """Empty registry has length 0."""
        registry = ScenarioRegistry()

        assert len(registry) == 0

    def test_register_scenario(self):
        """register() adds a scenario to the registry."""
        registry = ScenarioRegistry()
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")

        registry.register("test.echo", scenario)

        assert len(registry) == 1
        assert "test.echo" in registry

    def test_register_scenario_with_description(self):
        """register() stores the description."""
        registry = ScenarioRegistry()
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")

        registry.register("test.echo", scenario, description="Test echo scenario")

        entry = registry.get_entry("test.echo")
        assert entry.description == "Test echo scenario"

    def test_register_duplicate_raises_value_error(self):
        """register() raises ValueError for duplicate names."""
        registry = ScenarioRegistry()
        scenario1 = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        scenario2 = ExternalScenario(endpoint="http://localhost:3979/api/messages")

        registry.register("test.echo", scenario1)

        with pytest.raises(ValueError, match="Scenario 'test.echo' is already registered"):
            registry.register("test.echo", scenario2)

    def test_register_non_scenario_raises_type_error(self):
        """register() raises TypeError for non-Scenario objects."""
        registry = ScenarioRegistry()

        with pytest.raises(TypeError, match="scenario must be an instance of Scenario"):
            registry.register("test.echo", "not a scenario")

    def test_register_none_raises_type_error(self):
        """register() raises TypeError for None."""
        registry = ScenarioRegistry()

        with pytest.raises(TypeError, match="scenario must be an instance of Scenario"):
            registry.register("test.echo", None)

    def test_get_returns_scenario(self):
        """get() returns the registered scenario."""
        registry = ScenarioRegistry()
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        registry.register("test.echo", scenario)

        result = registry.get("test.echo")

        assert result is scenario

    def test_get_unknown_raises_key_error(self):
        """get() raises KeyError for unknown names."""
        registry = ScenarioRegistry()

        with pytest.raises(KeyError, match="Scenario 'unknown' not found"):
            registry.get("unknown")

    def test_get_shows_available_scenarios_in_error(self):
        """get() error message shows available scenarios."""
        registry = ScenarioRegistry()
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        registry.register("test.echo", scenario)

        with pytest.raises(KeyError, match="Available: test.echo"):
            registry.get("unknown")

    def test_get_shows_none_when_empty(self):
        """get() error message shows (none) when registry is empty."""
        registry = ScenarioRegistry()

        with pytest.raises(KeyError, match=r"Available: \(none\)"):
            registry.get("unknown")

    def test_get_entry_returns_full_entry(self):
        """get_entry() returns the full ScenarioEntry."""
        registry = ScenarioRegistry()
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        registry.register("test.echo", scenario, description="Test description")

        entry = registry.get_entry("test.echo")

        assert isinstance(entry, ScenarioEntry)
        assert entry.name == "test.echo"
        assert entry.scenario is scenario
        assert entry.description == "Test description"

    def test_get_entry_unknown_raises_key_error(self):
        """get_entry() raises KeyError for unknown names."""
        registry = ScenarioRegistry()

        with pytest.raises(KeyError, match="Scenario 'unknown' not found"):
            registry.get_entry("unknown")


# ============================================================================
# ScenarioRegistry Discovery Tests
# ============================================================================

class TestScenarioRegistryDiscovery:
    """Tests for ScenarioRegistry.discover() method."""

    def test_discover_all_with_default_pattern(self):
        """discover() returns all scenarios with default pattern."""
        registry = ScenarioRegistry()
        scenario1 = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        scenario2 = ExternalScenario(endpoint="http://localhost:3979/api/messages")
        registry.register("prod.echo", scenario1)
        registry.register("staging.echo", scenario2)

        result = registry.discover()

        assert len(result) == 2
        assert "prod.echo" in result
        assert "staging.echo" in result

    def test_discover_all_with_star_pattern(self):
        """discover('*') returns all scenarios."""
        registry = ScenarioRegistry()
        scenario1 = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        scenario2 = ExternalScenario(endpoint="http://localhost:3979/api/messages")
        registry.register("prod.echo", scenario1)
        registry.register("staging.echo", scenario2)

        result = registry.discover("*")

        assert len(result) == 2

    def test_discover_by_namespace(self):
        """discover('namespace.*') returns scenarios in namespace."""
        registry = ScenarioRegistry()
        scenario1 = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        scenario2 = ExternalScenario(endpoint="http://localhost:3979/api/messages")
        scenario3 = ExternalScenario(endpoint="http://localhost:3980/api/messages")
        registry.register("prod.echo", scenario1)
        registry.register("prod.multi", scenario2)
        registry.register("staging.echo", scenario3)

        result = registry.discover("prod.*")

        assert len(result) == 2
        assert "prod.echo" in result
        assert "prod.multi" in result
        assert "staging.echo" not in result

    def test_discover_by_suffix(self):
        """discover('*.suffix') returns scenarios with matching suffix."""
        registry = ScenarioRegistry()
        scenario1 = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        scenario2 = ExternalScenario(endpoint="http://localhost:3979/api/messages")
        scenario3 = ExternalScenario(endpoint="http://localhost:3980/api/messages")
        registry.register("prod.echo", scenario1)
        registry.register("staging.echo", scenario2)
        registry.register("prod.multi", scenario3)

        result = registry.discover("*.echo")

        assert len(result) == 2
        assert "prod.echo" in result
        assert "staging.echo" in result
        assert "prod.multi" not in result

    def test_discover_returns_entries(self):
        """discover() returns ScenarioEntry objects."""
        registry = ScenarioRegistry()
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        registry.register("test.echo", scenario, description="Test")

        result = registry.discover("test.*")

        assert isinstance(result["test.echo"], ScenarioEntry)
        assert result["test.echo"].description == "Test"

    def test_discover_empty_registry(self):
        """discover() returns empty dict for empty registry."""
        registry = ScenarioRegistry()

        result = registry.discover()

        assert result == {}

    def test_discover_no_matches(self):
        """discover() returns empty dict when no matches."""
        registry = ScenarioRegistry()
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        registry.register("prod.echo", scenario)

        result = registry.discover("staging.*")

        assert result == {}


# ============================================================================
# ScenarioRegistry Container Protocol Tests
# ============================================================================

class TestScenarioRegistryContainer:
    """Tests for ScenarioRegistry container protocol methods."""

    def test_contains_returns_true_for_registered(self):
        """__contains__ returns True for registered scenarios."""
        registry = ScenarioRegistry()
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        registry.register("test.echo", scenario)

        assert "test.echo" in registry

    def test_contains_returns_false_for_unregistered(self):
        """__contains__ returns False for unregistered scenarios."""
        registry = ScenarioRegistry()

        assert "test.echo" not in registry

    def test_len_returns_count(self):
        """__len__ returns the number of registered scenarios."""
        registry = ScenarioRegistry()
        scenario1 = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        scenario2 = ExternalScenario(endpoint="http://localhost:3979/api/messages")

        assert len(registry) == 0
        registry.register("test.echo", scenario1)
        assert len(registry) == 1
        registry.register("test.multi", scenario2)
        assert len(registry) == 2

    def test_iter_yields_entries(self):
        """__iter__ yields ScenarioEntry objects."""
        registry = ScenarioRegistry()
        scenario1 = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        scenario2 = ExternalScenario(endpoint="http://localhost:3979/api/messages")
        registry.register("test.echo", scenario1)
        registry.register("test.multi", scenario2)

        entries = list(registry)

        assert len(entries) == 2
        assert all(isinstance(e, ScenarioEntry) for e in entries)
        names = {e.name for e in entries}
        assert names == {"test.echo", "test.multi"}

    def test_iter_empty_registry(self):
        """__iter__ yields nothing for empty registry."""
        registry = ScenarioRegistry()

        entries = list(registry)

        assert entries == []

    def test_clear_removes_all(self):
        """clear() removes all registered scenarios."""
        registry = ScenarioRegistry()
        scenario1 = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        scenario2 = ExternalScenario(endpoint="http://localhost:3979/api/messages")
        registry.register("test.echo", scenario1)
        registry.register("test.multi", scenario2)

        registry.clear()

        assert len(registry) == 0
        assert "test.echo" not in registry
        assert "test.multi" not in registry


# ============================================================================
# Global scenario_registry Tests
# ============================================================================

class TestGlobalScenarioRegistry:
    """Tests for the global scenario_registry instance."""

    def setup_method(self):
        """Clear the global registry before each test."""
        scenario_registry.clear()

    def teardown_method(self):
        """Clear the global registry after each test."""
        scenario_registry.clear()

    def test_global_registry_is_singleton(self):
        """scenario_registry is a ScenarioRegistry instance."""
        assert isinstance(scenario_registry, ScenarioRegistry)

    def test_global_registry_can_register_and_get(self):
        """Global registry supports register and get operations."""
        scenario = ExternalScenario(endpoint="http://localhost:3978/api/messages")

        scenario_registry.register("test.echo", scenario)
        result = scenario_registry.get("test.echo")

        assert result is scenario


# ============================================================================
# load_scenarios Tests with Temporary Files
# ============================================================================

class TestLoadScenarios:
    """Tests for load_scenarios function using temporary files."""

    def setup_method(self):
        """Clear the global registry before each test."""
        scenario_registry.clear()

    def teardown_method(self):
        """Clear the global registry after each test."""
        scenario_registry.clear()

    def test_load_scenarios_from_file_path(self):
        """load_scenarios() loads scenarios from a .py file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a scenario file
            scenario_file = Path(tmpdir) / "test_scenarios.py"
            scenario_file.write_text(
                """
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.core import ExternalScenario

scenario_registry.register(
    "loaded.echo",
    ExternalScenario(endpoint="http://localhost:3978/api/messages"),
    description="Loaded from file",
)
"""
            )

            count = load_scenarios(str(scenario_file))

            assert count == 1
            assert "loaded.echo" in scenario_registry
            entry = scenario_registry.get_entry("loaded.echo")
            assert entry.description == "Loaded from file"

    def test_load_scenarios_multiple_registrations(self):
        """load_scenarios() returns count of newly registered scenarios."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_file = Path(tmpdir) / "multi_scenarios.py"
            scenario_file.write_text(
                """
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.core import ExternalScenario

scenario_registry.register(
    "loaded.one",
    ExternalScenario(endpoint="http://localhost:3978/api/messages"),
)
scenario_registry.register(
    "loaded.two",
    ExternalScenario(endpoint="http://localhost:3979/api/messages"),
)
scenario_registry.register(
    "loaded.three",
    ExternalScenario(endpoint="http://localhost:3980/api/messages"),
)
"""
            )

            count = load_scenarios(str(scenario_file))

            assert count == 3
            assert "loaded.one" in scenario_registry
            assert "loaded.two" in scenario_registry
            assert "loaded.three" in scenario_registry

    def test_load_scenarios_file_not_found(self):
        """load_scenarios() returns 0 when file not found."""
        count = load_scenarios("/nonexistent/path/scenarios.py")

        assert count == 0

    def test_load_scenarios_with_forward_slashes(self):
        """load_scenarios() handles file paths with forward slashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_file = Path(tmpdir) / "slash_scenarios.py"
            scenario_file.write_text(
                """
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.core import ExternalScenario

scenario_registry.register(
    "slash.echo",
    ExternalScenario(endpoint="http://localhost:3978/api/messages"),
)
"""
            )

            # Use forward slashes in path
            forward_slash_path = str(scenario_file).replace("\\", "/")
            count = load_scenarios(forward_slash_path)

            assert count == 1
            assert "slash.echo" in scenario_registry

    def test_load_scenarios_with_backslashes(self):
        """load_scenarios() handles file paths with backslashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_file = Path(tmpdir) / "backslash_scenarios.py"
            scenario_file.write_text(
                """
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.core import ExternalScenario

scenario_registry.register(
    "backslash.echo",
    ExternalScenario(endpoint="http://localhost:3978/api/messages"),
)
"""
            )

            # Use backslashes in path (Windows style)
            backslash_path = str(scenario_file).replace("/", "\\")
            count = load_scenarios(backslash_path)

            assert count == 1
            assert "backslash.echo" in scenario_registry

    def test_load_scenarios_existing_scenarios_not_counted(self):
        """load_scenarios() only counts newly registered scenarios."""
        # Register one scenario first
        existing = ExternalScenario(endpoint="http://localhost:3978/api/messages")
        scenario_registry.register("existing.echo", existing)

        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_file = Path(tmpdir) / "new_scenarios.py"
            scenario_file.write_text(
                """
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.core import ExternalScenario

scenario_registry.register(
    "new.echo",
    ExternalScenario(endpoint="http://localhost:3979/api/messages"),
)
"""
            )

            count = load_scenarios(str(scenario_file))

            assert count == 1  # Only the new one
            assert len(scenario_registry) == 2  # Total is 2

    def test_load_scenarios_with_syntax_error(self):
        """load_scenarios() returns 0 when file has syntax error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_file = Path(tmpdir) / "broken_scenarios.py"
            scenario_file.write_text(
                """
this is not valid python syntax!!!
"""
            )

            count = load_scenarios(str(scenario_file))

            assert count == 0

    def test_load_scenarios_with_import_error(self):
        """load_scenarios() returns 0 when file has import error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_file = Path(tmpdir) / "import_error_scenarios.py"
            scenario_file.write_text(
                """
from nonexistent_module import something
"""
            )

            count = load_scenarios(str(scenario_file))

            assert count == 0

    def test_load_scenarios_cleans_up_sys_path(self):
        """load_scenarios() does not permanently modify sys.path."""
        original_path = sys.path.copy()

        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_file = Path(tmpdir) / "cleanup_scenarios.py"
            scenario_file.write_text(
                """
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.core import ExternalScenario

scenario_registry.register(
    "cleanup.echo",
    ExternalScenario(endpoint="http://localhost:3978/api/messages"),
)
"""
            )

            load_scenarios(str(scenario_file))

            # sys.path should not contain the temp directory
            assert tmpdir not in sys.path
            # sys.path length might differ due to imports, but tmpdir should be removed
            assert all(tmpdir not in p for p in sys.path)

    def test_load_scenarios_in_subdirectory(self):
        """load_scenarios() loads from files in subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "subdir" / "nested"
            subdir.mkdir(parents=True)
            scenario_file = subdir / "deep_scenarios.py"
            scenario_file.write_text(
                """
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.core import ExternalScenario

scenario_registry.register(
    "deep.echo",
    ExternalScenario(endpoint="http://localhost:3978/api/messages"),
)
"""
            )

            count = load_scenarios(str(scenario_file))

            assert count == 1
            assert "deep.echo" in scenario_registry

    def test_load_scenarios_relative_path(self):
        """load_scenarios() handles relative paths."""
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_file = Path(tmpdir) / "relative_scenarios.py"
            scenario_file.write_text(
                """
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.core import ExternalScenario

scenario_registry.register(
    "relative.echo",
    ExternalScenario(endpoint="http://localhost:3978/api/messages"),
)
"""
            )

            # Change to temp directory and use relative path
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                count = load_scenarios("./relative_scenarios.py")

                assert count == 1
                assert "relative.echo" in scenario_registry
            finally:
                os.chdir(original_cwd)


# ============================================================================
# load_scenarios Module Path Tests
# ============================================================================

class TestLoadScenariosModulePath:
    """Tests for load_scenarios with module paths."""

    def setup_method(self):
        """Clear the global registry before each test."""
        scenario_registry.clear()

    def teardown_method(self):
        """Clear the global registry after each test."""
        scenario_registry.clear()
        # Clean up any test modules from sys.modules
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith("test_module_")]
        for mod in modules_to_remove:
            del sys.modules[mod]

    def test_load_scenarios_from_module_path(self):
        """load_scenarios() loads scenarios from a module path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a module
            module_dir = Path(tmpdir)
            module_file = module_dir / "test_module_scenarios.py"
            module_file.write_text(
                """
from microsoft_agents.testing.scenario_registry import scenario_registry
from microsoft_agents.testing.core import ExternalScenario

scenario_registry.register(
    "module.echo",
    ExternalScenario(endpoint="http://localhost:3978/api/messages"),
)
"""
            )

            # Add to sys.path temporarily
            sys.path.insert(0, tmpdir)
            try:
                count = load_scenarios("test_module_scenarios")

                assert count == 1
                assert "module.echo" in scenario_registry
            finally:
                sys.path = [p for p in sys.path if p != tmpdir]

    def test_load_scenarios_nonexistent_module(self):
        """load_scenarios() returns 0 for nonexistent module."""
        count = load_scenarios("nonexistent_module_12345")

        assert count == 0
