# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel


class SigninStateVerificationQuery(BaseModel):
    """Represents the state verification query for sign-in.

    :param state: The state value used for verification.
    :type state: str
    """

    state: str = None
