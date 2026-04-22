# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Task Module UI constants for Teams applications."""

from .task_module_ids import TaskModuleIds
from .ui_settings import UISettings


class TaskModuleUIConstants:
    """
    Class containing UI settings constants for various Task Modules.
    """

    AdaptiveCard: UISettings = UISettings(
        width=400,
        height=200,
        title="Adaptive Card: Inputs",
        id=TaskModuleIds.AdaptiveCard,
        button_title="Adaptive Card",
    )

    YouTube: UISettings = UISettings(
        width=1000,
        height=700,
        title="You Tube Video",
        id=TaskModuleIds.YouTube,
        button_title="You Tube",
    )

    CustomForm: UISettings = UISettings(
        width=510,
        height=450,
        title="Custom Form",
        id=TaskModuleIds.CustomForm,
        button_title="Custom Form",
    )
