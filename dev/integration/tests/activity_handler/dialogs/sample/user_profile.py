# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from microsoft_agents.activity import Attachment


@dataclass
class UserProfile:
    """User profile collected by UserProfileDialog."""

    name: str | None = None
    transport: str | None = None
    age: int = 0
    picture: Attachment | None = None
