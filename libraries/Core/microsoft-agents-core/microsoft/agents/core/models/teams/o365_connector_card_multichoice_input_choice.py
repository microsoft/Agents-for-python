# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel


class O365ConnectorCardMultichoiceInputChoice(BaseModel):
    """O365 connector card multichoice input choice.

    :param display: Display text for the choice.
    :type display: str
    :param value: Value for the choice.
    :type value: str
    """

    display: str = None
    value: str = None
