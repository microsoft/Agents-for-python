# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import AgentsModel, Activity


class ExecuteTurnRequest(AgentsModel):

    activity: Activity
