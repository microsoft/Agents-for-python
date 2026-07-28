"""Test scenario registry for AgentApplication-based integration tests."""

from microsoft_agents.testing import (
    AiohttpScenario,
    ScenarioConfig,
    Scenario,
)

from .quickstart import init_agent as init_quickstart

_SCENARIO_INITS = {
    "quickstart": init_quickstart,
}


def load_scenario(
    name: str,
    config: ScenarioConfig | None = None,
    use_jwt_middleware: bool = False,
) -> Scenario:
    """Load a named scenario by key."""
    name = name.lower()

    if name not in _SCENARIO_INITS:
        raise ValueError(f"Unknown scenario: {name}")

    return AiohttpScenario(
        _SCENARIO_INITS[name],
        config=config,
        use_jwt_middleware=use_jwt_middleware,
    )


__all__ = [
    "load_scenario",
]
