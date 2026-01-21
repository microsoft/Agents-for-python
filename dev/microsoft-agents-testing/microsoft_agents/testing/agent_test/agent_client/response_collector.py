from microsoft_agents.activity import (
    Activity,
    InvokeResponse,
)

from microsoft_agents.testing.check import Check

class ResponseCollector:

    def __init__(self, filter: Check | None = None):
        self._filter = filter
        self._activities: list[Activity] = []
        self._invoke_responses: list[InvokeResponse] = []

    def add(self, response: Activity | InvokeResponse) -> None:
        if self._filter and not self._filter.matches(response):
            return
        
        if isinstance(response, Activity):
            self._activities.append(response)
        elif isinstance(response, InvokeResponse):
            self._invoke_responses.append(response)

    def get_activities(self) -> list[Activity]:
        return list(self._activities)
    
    def get_invoke_responses(self) -> list[InvokeResponse]:
        return list(self._invoke_responses)