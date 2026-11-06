# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import StrEnum


class InputHints(StrEnum):
    accepting_input = "acceptingInput"
    ignoring_input = "ignoringInput"
    expecting_input = "expectingInput"
