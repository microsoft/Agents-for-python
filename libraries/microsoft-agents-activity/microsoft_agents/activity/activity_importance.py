# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class ActivityImportance(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
