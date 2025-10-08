# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class ActivityEventNames(str, Enum):
    continue_conversation = "ContinueConversation"
    create_conversation = "CreateConversation"
