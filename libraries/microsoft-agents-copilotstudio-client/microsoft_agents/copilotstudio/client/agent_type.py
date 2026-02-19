# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class AgentType(str, Enum):
    PUBLISHED = "published"
    PREBUILT = "prebuilt"
