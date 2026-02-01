# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Predefined test scenarios for the CLI.

Provides ready-to-use scenario configurations for common testing patterns.
"""

from .auth_scenario import auth_scenario
from .basic_scenario import basic_scenario

SCENARIOS = {
    "auth": auth_scenario,
    "basic": basic_scenario,
}

__all__ = [
    "SCENARIOS",
]