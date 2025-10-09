# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class InstallationUpdateActionTypes(str, Enum):
    add = "add"
    remove = "remove"
