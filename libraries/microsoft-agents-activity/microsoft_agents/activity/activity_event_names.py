# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import StrEnum


class ActivityEventNames(StrEnum):
    continue_conversation = "ContinueConversation"
    create_conversation = "CreateConversation"
