# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import StrEnum


class InstallationUpdateActionTypes(StrEnum):
    add = "add"
    remove = "remove"
