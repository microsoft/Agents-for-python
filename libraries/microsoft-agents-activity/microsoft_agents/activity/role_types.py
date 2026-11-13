# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import StrEnum


class RoleTypes(StrEnum):
    user = "user"
    agent = "bot"
    skill = "skill"
    connector_user = "connectoruser"
    agentic_identity = "agenticAppInstance"
    agentic_user = "agenticUser"
