import asyncio

from copy import deepcopy
from typing import Awaitable, Callable

from microsoft_agents.activity import Activity

from microsoft_agents.testing.assertions import assert_activity

class DataDrivenTest:

    def __init__(self, test_flow: dict) -> None:
        self._description = test_flow.get("description", "")

        defaults = test_flow.get("defaults", {})
        self._input_defaults = defaults.get("input", {})
        self._assertion_defaults = defaults.get("assertion", {})
        self._sleep_defaults = defaults.get("sleep", {})        

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

    async def run(self, agent_client, response_client) -> None:
        
        for step in self._test:
            step_type = step.get("type")
            if not step_type:
                raise ValueError("Each step must have a 'type' field.")
            
            if step_type == "input":
                input_activity = self._load_input(step)
                await agent_client.send_activity(input_activity)
            elif step_type == "assertion":
                assertion = self._load_assertion(step)
                responses = await response_client.pop()

                selector = Selector(assertion.get("selector", {}))
                selection = selector.select(responses)

                assert_activity(selection, assertion)

            elif step_type == "sleep":
                await self._sleep(step)