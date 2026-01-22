from typing import Any

from microsoft_agents.activity import (
    Activity,
    InvokeResponse,
)

class ResponseCollector:

    def __init__(self):
        self._activities: list[Activity] = []
        self._invoke_responses: list[InvokeResponse] = []

        self._pop_index = 0

    def add(self, response: Any) -> bool:
        
        if isinstance(response, Activity):
            self._activities.append(response)
        elif isinstance(response, InvokeResponse):
            self._invoke_responses.append(response)
        else:
            return False
        
        return True

    def get_activities(self) -> list[Activity]:
        self._pop_index = len(self._activities)
        return list(self._activities)
    
    def get_invoke_responses(self) -> list[InvokeResponse]:
        return list(self._invoke_responses)
    
    def pop(self) -> list[Activity]:
        new_activities = self._activities[self._pop_index :]
        self._pop_index = len(self._activities)
        return new_activities