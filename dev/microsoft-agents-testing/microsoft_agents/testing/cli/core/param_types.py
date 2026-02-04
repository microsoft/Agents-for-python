from microsoft_agents.testing.core import (
    Scenario,
    AiohttpScenario,
    ExternalScenario,
)

import click

class ScenarioParamType(click.ParamType):
    name = "scenario"

    def convert(self, value, param, ctx) -> Scenario:
        if "http" in 