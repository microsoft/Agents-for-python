# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Predefined test scenarios for the CLI.

Provides ready-to-use scenario configurations for common testing patterns.
"""

from .auth_scenario import auth_scenario
from .basic_scenario import basic_scenario, basic_scenario_no_auth

SCENARIOS = [
    ["auth", auth_scenario, "Authentication testing scenario with dynamic auth routes"],
    ["basic", basic_scenario, "Basic message handling scenario"],
    ["basic_no_auth", basic_scenario_no_auth, "Basic message handling scenario without JWT authentication"],
]