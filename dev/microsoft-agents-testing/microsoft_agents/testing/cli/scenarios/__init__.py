from .auth_scenario import auth_scenario
from .basic_scenario import basic_scenario

SCENARIOS = {
    "auth": auth_scenario,
    "basic": basic_scenario,
}

__all__ = [
    "SCENARIOS",
]