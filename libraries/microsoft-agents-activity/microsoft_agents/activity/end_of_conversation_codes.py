# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class EndOfConversationCodes(str, Enum):
    unknown = "unknown"
    completed_successfully = "completedSuccessfully"
    user_cancelled = "userCancelled"
    timed_out = "botTimedOut"
    issued_invalid_message = "botIssuedInvalidMessage"
    channel_failed = "channelFailed"
