# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.s

import pytest
import asyncio

from copy import deepcopy

from microsoft_agents.activity import Activity, DeliveryModes, InvokeResponse

from microsoft_agents.testing.assertions import ModelAssertion
from microsoft_agents.testing.utils import (
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
        for i, step in enumerate(self._test):
            
            if isinstance(step, str):
                self._test[i] = {"type": step}
                continue

            if step.get("type") == "assertion":
                if "assertion" not in step:
                    if "activity" in step:
                        step["assertion"] = step["activity"]
                        step["assertion_type"] = "activity"
                    elif "invokeResponse" in step:
                        step["assertion"] = step["invokeResponse"]
                        step["assertion_type"] = "invoke_response"
                    elif "invoke_response" in step:
                        step["assertion"] = step["invoke_response"]
                        step["assertion_type"] = "invoke_response"
                    else:
                        step["assertion"] = {}
                        step["assertion_type"] = "activity"
                        
                selector = step.get("selector")
                if selector is not None:
                    if isinstance(selector, int):
                        step["selector"] = {"index": selector}
                    elif isinstance(selector, dict):
                        if "selector" not in selector:
                            if "activity" in selector:
                                selector["model"] = selector["activity"]
                            elif "invokeResponse" in selector:
                                selector["model"] = selector["invokeResponse"]
                            elif "invoke_response" in selector:
                                selector["model"] = selector["invoke_response"]

    async def _run_input(
        self,
        step: dict,
        responses: list[Activity],
        invoke_responses: list[InvokeResponse],
        agent_client: AgentClient,
        response_client: ResponseClient,
    ) -> None:
        input_activity = self._load_input(step)

        if input_activity.delivery_mode == DeliveryModes.expect_replies:
            replies = await agent_client.send_expect_replies(input_activity)
            responses.extend(replies)
        elif input_activity.delivery_mode == DeliveryModes.stream:
            # async for reply in agent_client.send_stream_activity(input_activity):
            #     responses.append(reply)
            raise NotImplementedError("Stream delivery mode is not implemented yet.")
        elif input_activity.type == "invoke":
            invoke_response = await agent_client.send_invoke_activity(input_activity)
            invoke_responses.append(invoke_response)
        else:
            await agent_client.send_activity(input_activity)

    async def _run_assertion(
        self,
        step: dict,
        responses: list[Activity],
        invoke_responses: list[InvokeResponse],
        agent_client: AgentClient,
        response_client: ResponseClient,
    ) -> None:

        assertion = self._load_assertion(step)
        responses.extend(await response_client.pop())

        model_list: list

        if step.get("assertion_type") == "activity":
            model_list = responses

        if step.get("assertion_type") == "invoke_response":
            model_list = invoke_responses

        res, err = assertion.check(model_list)

        if not res:
            err = "Assertion failed: {}\n\n{}".format(step, err)
            assert res, err

    async def run(
        self, agent_client: AgentClient, response_client: ResponseClient
    ) -> None:
        """Run the data driven test.

        :param agent_client: The agent client to send activities to.
        """

        self._pre_process()

        responses: list[Activity] = []
        invoke_responses: list[InvokeResponse] = []
        for step in self._test:
            step_type = step.get("type")
            if not step_type:
                raise ValueError("Each step must have a 'type' field.")

            if step_type == "input":
                await self._run_input(
                    step, responses, invoke_responses, agent_client, response_client
                )

            elif step_type == "assertion":
                await self._run_assertion(
                    step, responses, invoke_responses, agent_client, response_client
                )

            elif step_type == "sleep":
                await self._sleep(step)

            elif step_type == "breakpoint":
                breakpoint()

            elif step_type == "skip":
                pytest.skip("Skipping step as per test definition.")
