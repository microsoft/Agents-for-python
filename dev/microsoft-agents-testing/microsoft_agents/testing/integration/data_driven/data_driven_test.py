# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.s

import asyncio

import yaml

from copy import deepcopy

from microsoft_agents.activity import Activity

from microsoft_agents.testing.assertions import ActivityAssertion
from microsoft_agents.testing.utils import (
    populate_activity,
    update_with_defaults,
)

from ..core import AgentClient, ResponseClient

class DataDrivenTest:
    """Data driven test runner."""

    def __init__(self, test_flow: dict) -> None:
        self._description = test_flow.get("description", "")

        defaults = test_flow.get("defaults", {})
        self._input_defaults = defaults.get("input", {})
        self._assertion_defaults = defaults.get("assertion", {})
        self._sleep_defaults = defaults.get("sleep", {})

        parent = test_flow.get("parent")
        if parent:
            with open(parent, "r", encoding="utf-8") as f:
                parent_flow = yaml.safe_load(f)
                input_defaults = parent_flow.get("defaults", {}).get("input", {})
                sleep_defaults = parent_flow.get("defaults", {}).get("sleep", {})
                assertion_defaults = parent_flow.get("defaults", {}).get(
                    "assertion", {}
                )

                self._input_defaults = {**input_defaults, **self._input_defaults}
                self._sleep_defaults = {**sleep_defaults, **self._sleep_defaults}
                self._assertion_defaults = {
                    **assertion_defaults,
                    **self._assertion_defaults,
                }

        self._test = test_flow.get("test", [])

    def _load_input(self, input_data: dict) -> Activity:
        data = deepcopy(self._input_defaults)
        data.update(input_data)
        return Activity.model_validate(data)

    def _load_assertion(self, assertion_data: dict) -> dict:
        data = deepcopy(self._assertion_defaults)
        data.update(assertion_data)
        return data

    async def _sleep(self, sleep_data: dict) -> None:
        duration = sleep_data.get("duration")
        if duration is None:
            duration = self._sleep_defaults.get("duration", 0)
        await asyncio.sleep(duration)

    async def run(self, agent_client: AgentClient, response_client: ResponseClient) -> None:
        """Run the data driven test.
        
        :param agent_client: The agent client to send activities to.
        """

        responses = []
        for step in self._test:
            step_type = step.get("type")
            if not step_type:
                raise ValueError("Each step must have a 'type' field.")

            if step_type == "input":
                input_activity = self._load_input(step)
                populate_activity(input_activity, self._input_defaults)
                await agent_client.send_activity(input_activity)
            elif step_type == "assertion":

                assertion = self._load_assertion(step)
                update_with_defaults(assertion, self._assertion_defaults)
                
                activity_assertion = ActivityAssertion.from_config(assertion)

                responses.extend(await response_client.pop())

                assert activity_assertion(responses)

            elif step_type == "sleep":
                await self._sleep(step)
