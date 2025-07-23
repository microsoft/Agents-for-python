# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""UI Settings model for Teams task modules."""

from typing import Optional


class UISettings:
    """
    Settings for configuring UI elements in Teams task modules.

    Attributes:
        height: The height of the UI element.
        width: The width of the UI element.
        title: The title to display.
        button_title: The text to display on the button.
        id: The identifier for the UI element.
    """

    def __init__(
        self,
        height: Optional[int] = None,
        width: Optional[int] = None,
        title: Optional[str] = None,
        button_title: Optional[str] = None,
        id: Optional[str] = None,
    ):
        """
        Initialize UISettings with optional parameters.
        Args:
            height: The height of the UI element.
            width: The width of the UI element.
            title: The title to display.
            button_title: The text to display on the button.
            id: The identifier for the UI element.
        """
        self.height = height
        self.width = width
        self.title = title
        self.button_title = button_title
        self.id = id
