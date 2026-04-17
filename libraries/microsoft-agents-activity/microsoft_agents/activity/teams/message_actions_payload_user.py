# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Annotated

from pydantic import Field
from ..agents_model import AgentsModel


class MessageActionsPayloadUser(AgentsModel):
    """Represents a user entity.

    :param user_identity_type: The identity type of the user. Possible values include: 'aadUser', 'onPremiseAadUser', 'anonymousGuest', 'federatedUser'
    :type user_identity_type: str | None
    :param id: The id of the user.
    :type id: str | None
    :param display_name: The plaintext display name of the user.
    :type display_name: str | None
    """

    user_identity_type: (
        Annotated[
            str,
            Field(pattern=r"^(aadUser|onPremiseAadUser|anonymousGuest|federatedUser)$"),
        ]
        | None
    )
    id: str | None
    display_name: str | None
