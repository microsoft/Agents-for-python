# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Optional

from pydantic import ConfigDict
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class ChannelAccount(AgentsModel):
    """Channel account information needed to route a message.

    :param id: Channel id for the user or agent on this channel (Example:
     ``joe@smith.com``, or ``@joesmith`` or ``123456``)
    :type id: str
    :param name: Display friendly name
    :type name: str
    :param aad_object_id: This account's object ID within Azure Active
     Directory (AAD)
    :type aad_object_id: str
    :param role: Role of the entity behind the account
    :type role: str or ~microsoft_agents.activity.RoleTypes
    """

    model_config = ConfigDict(extra="allow")

    id: NonEmptyString = None
    name: str = None
    aad_object_id: Optional[NonEmptyString] = None
    role: Optional[NonEmptyString] = None
    agentic_user_id: Optional[NonEmptyString] = None
    agentic_app_id: Optional[NonEmptyString] = None
    tenant_id: Optional[NonEmptyString] = None

    @property
    def properties(self) -> dict[str, Any]:
        """Returns the set of properties that are not None."""
        return self.model_extra
