# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class O365ConnectorCardOpenUriTarget(AgentsModel):
    """O365 connector card OpenUri target.

    :param os: Target operating system. Possible values include: 'default', 'iOS', 'android', 'windows'
    :type os: str
    :param uri: Target URI.
    :type uri: str
    """

    os: str = None
    uri: str = None
