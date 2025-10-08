# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class SemanticActionsStates(str, Enum):
    start_action = "start"
    continue_action = "continue"
    done_action = "done"
