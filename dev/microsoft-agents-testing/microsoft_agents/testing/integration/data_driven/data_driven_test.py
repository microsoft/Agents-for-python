# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.s

import pytest
import asyncio

import yaml

from copy import deepcopy

from microsoft_agents.activity import Activity

from microsoft_agents.testing.assertions import ModelAssertion
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
            parent_assertion_defaults = parent.get("defaults", {}).get("assertion", {})

            update_with_defaults(self._input_defaults, parent_input_defaults)
            update_with_defaults(self._sleep_defaults, parent_sleep_defaults)
            update_with_defaults(self._assertion_defaults, parent_assertion_defaults)

        self._test = test_flow.get("test", [])

    @property
    def name(self) -> str:
        """Get the name of the data driven test."""
        return self._name

    def _load_input(self, input_data: dict) -> Activity:
        defaults = deepcopy(self._input_defaults)
        update_with_defaults(input_data, defaults)
        return Activity.model_validate(input_data.get("activity", {}))

    def _load_assertion(self, assertion_data: dict) -> ModelAssertion:
        defaults = deepcopy(self._assertion_defaults)
        update_with_defaults(assertion_data, defaults)
        return ModelAssertion.from_config(assertion_data)

    async def _sleep(self, sleep_data: dict) -> None:
        duration = sleep_data.get("duration")
        if duration is None:
            duration = self._sleep_defaults.get("duration", 0)
        await asyncio.sleep(duration)

    def _pre_process(self) -> None:
        """Compile the data driven test to ensure all steps are valid."""
        for step in self._test:
            if step.get("type") == "assertion":
                if "assertion" not in step:
                    if "activity" in step:
                        step["assertion"] = step["activity"]
                selector = step.get("selector")
                if selector is not None:
                    if isinstance(selector, int):
                        step["selector"] = {"index": selector}
                    elif isinstance(selector, dict):
                        if "selector" not in selector:
                            if "activity" in selector:
                                selector["selector"] = selector["activity"]

    async def run(
        self, agent_client: AgentClient, response_client: ResponseClient
    ) -> None:
        """Run the data driven test.

        :param agent_client: The agent client to send activities to.
        """

        self._pre_process()

        responses = []
        for step in self._test:
            step_type = step.get("type")
            if not step_type:
                raise ValueError("Each step must have a 'type' field.")

            if step_type == "input":
                input_activity = self._load_input(step)
                if input_activity.delivery_mode == "expectReplies":
                    replies = await agent_client.send_expect_replies(input_activity)
                    responses.extend(replies)
                else:
                    await agent_client.send_activity(input_activity)

            elif step_type == "assertion":
                activity_assertion = self._load_assertion(step)
                responses.extend(await response_client.pop())

                res, err = activity_assertion.check(responses)

                if not res:
                    err = "Assertion failed: {}\n\n{}".format(step, err)
                    assert res, err

            elif step_type == "sleep":
                await self._sleep(step)

            elif step_type == "breakpoint":
                breakpoint()

            elif step_type == "skip":
                pytest.skip("Skipping step as per test definition.")
