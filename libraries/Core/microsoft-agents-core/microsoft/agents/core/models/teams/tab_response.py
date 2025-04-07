# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel

from .tab_response_payload import TabResponsePayload


class TabResponse(BaseModel):
    """Envelope for Card Tab Response Payload.

    :param tab: Possible values include: 'continue', 'auth' or 'silentAuth'
    :type type: TabResponsePayload
    """

    tab: TabResponsePayload = None
