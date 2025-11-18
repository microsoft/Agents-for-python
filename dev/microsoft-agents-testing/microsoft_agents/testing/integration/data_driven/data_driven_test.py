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
        self._name: str = test_flow.get("name", "")
        if not self._name:
            raise ValueError("Test flow must have a 'name' field.")
        self._description = test_flow.get("description", "")

        defaults = test_flow.get("defaults", {})
        self._input_defaults = defaults.get("input", {})
        self._assertion_defaults = defaults.get("assertion", {})
        self._sleep_defaults = defaults.get("sleep", {})

        parent = test_flow.get("parent")
        if parent:
            parent_input_defaults = parent.get("defaults", {}).get("input", {})
            parent_sleep_defaults = parent.get("defaults", {}).get("sleep", {})
            parent_assertion_defaults = parent.get("defaults", {}).get(
                "assertion", {}
            )

            update_with_defaults(self._input_defaults, parent_input_defaults)
            update_with_defaults(self._sleep_defaults, parent_sleep_defaults)
            update_with_defaults(
                self._assertion_defaults, parent_assertion_defaults
            )

        self._test = test_flow.get("test", [])

    @property
    def name(self) -> str:
        """Get the name of the data driven test."""
        return self._name

    def _load_input(self, input_data: dict) -> Activity:
        defaults = deepcopy(self._input_defaults)
        update_with_defaults(input_data, defaults)
        return Activity.model_validate(input_data.get("activity", {}))

    def _load_assertion(self, assertion_data: dict) -> ActivityAssertion:
        defaults = deepcopy(self._assertion_defaults)
        update_with_defaults(assertion_data, defaults)
        return ActivityAssertion.from_config(assertion_data)

    async def _sleep(self, sleep_data: dict) -> None:
        duration = sleep_data.get("duration")
        if duration is None:
            duration = self._sleep_defaults.get("duration", 0)
        await asyncio.sleep(duration)

    async def run(
        self, agent_client: AgentClient, response_client: ResponseClient
    ) -> None:
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
                await agent_client.send_activity(input_activity)

            elif step_type == "assertion":
                activity_assertion = self._load_assertion(step)
                responses.extend(await response_client.pop())
                activity_assertion(responses)

            elif step_type == "sleep":
                await self._sleep(step)
