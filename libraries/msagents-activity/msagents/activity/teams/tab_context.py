# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class TabContext(AgentsModel):
    """Current tab request context, i.e., the current theme.

    :param theme: Gets or sets the current user's theme.
    :type theme: str
    """

    theme: str = None
