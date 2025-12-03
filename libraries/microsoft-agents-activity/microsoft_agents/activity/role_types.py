# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class RoleTypes(str, Enum):
    user = "user"
    agent = "bot"
    skill = "skill"
    connector_user = "connectoruser"
    agentic_identity = "agenticAppInstance"
    agentic_user = "agenticUser"
