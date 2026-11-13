# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import StrEnum


class AgentType(StrEnum):
    PUBLISHED = "published"
    PREBUILT = "prebuilt"
