# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from microsoft_agents.activity import (
    Activity,
    InvokeResponse,
)

class ResponseCollector:
    """Collects Activities and InvokeResponses."""

    def __init__(self):
        """Initializes empty collections for activities and invoke responses."""
        self._activities: list[Activity] = []
        self._invoke_responses: list[InvokeResponse] = []

        self._pop_index = 0

    def add(self, response: Any) -> bool:
        """Adds an Activity or InvokeResponse to the appropriate collection.
        
        :param response: The Activity or InvokeResponse to add.
        :return: True if the response was added successfully, False otherwise.
        """
        
        if isinstance(response, Activity):
            self._activities.append(response)
        elif isinstance(response, InvokeResponse):
            self._invoke_responses.append(response)
        else:
            return False
        
        return True

    def get_activities(self) -> list[Activity]:
        """Returns all collected activities.
        
        Resets the pop index to the end of the activities list.
        """
        self._pop_index = len(self._activities)
        return list(self._activities)
    
    def get_invoke_responses(self) -> list[InvokeResponse]:
        """Returns all collected invoke responses."""
        return list(self._invoke_responses)
    
    def pop(self) -> list[Activity]:
        """Returns new activities since the last pop call.
        
        :return: List of new Activities added since the last pop.
        """
        new_activities = self._activities[self._pop_index :]
        self._pop_index = len(self._activities)
        return new_activities