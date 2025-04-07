# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel
from typing import Annotated, Optional


class MessageActionsPayloadUser(AgentsModel):
    """Represents a user entity.

    :param user_identity_type: The identity type of the user. Possible values include: 'aadUser', 'onPremiseAadUser', 'anonymousGuest', 'federatedUser'
    :type user_identity_type: Optional[str]
    :param id: The id of the user.
    :type id: Optional[str]
    :param display_name: The plaintext display name of the user.
    :type display_name: Optional[str]
    """

    user_identity_type: Optional[
        Annotated[
            str,
            Field(pattern=r"^(aadUser|onPremiseAadUser|anonymousGuest|federatedUser)$"),
        ]
    ]
    id: Optional[str]
    display_name: Optional[str]
