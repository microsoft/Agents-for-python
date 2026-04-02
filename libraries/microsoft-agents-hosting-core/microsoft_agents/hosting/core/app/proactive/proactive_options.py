"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from microsoft_agents.hosting.core.storage import Storage


@dataclass
class ProactiveOptions:
    """
    Options for the Proactive messaging subsystem.

    :param storage: The storage instance used to persist and retrieve conversations.
    :type storage: Optional[:class:`microsoft_agents.hosting.core.storage.Storage`]
    :param fail_on_unsigned_in_connections: If ``True`` (the default), a
        :exc:`RuntimeError` is raised when a required OAuth token is not available
        during a proactive continuation.  Set to ``False`` to silently skip the
        handler instead.
    :type fail_on_unsigned_in_connections: bool
    """

    storage: Optional[Storage] = None
    """Storage used to persist Conversation objects."""

    fail_on_unsigned_in_connections: bool = True
    """
    When ``True`` (default), raise an error if a required OAuth connection is
    not signed-in at the time a proactive continuation runs.
    """
