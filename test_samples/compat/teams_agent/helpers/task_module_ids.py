# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Task Module ID constants."""

from enum import Enum


class TaskModuleIds(str, Enum):
    """
    Class containing constants for Task Module IDs.
    """

    AdaptiveCard = "AdaptiveCard"
    YouTube = "YouTube"
    CustomForm = "CustomForm"
