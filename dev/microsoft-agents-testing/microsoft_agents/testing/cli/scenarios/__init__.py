from .auth_scenario import AuthScenario
from .basic_scenario import BasicScenario

SCENARIOS = {
    "auth": AuthScenario,
    "basic": BasicScenario,
}

__all__ = [
    "SCENARIOS",
]