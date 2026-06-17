# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import TurnContext

class TeamsTurnContext(TurnContext):
    """A context object for handling Teams-specific turn functionality."""
    
    def __init__(self, context: TurnContext):
        super().__init__(context)

        self._context = context