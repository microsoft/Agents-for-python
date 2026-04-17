# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class FileInfoCard(AgentsModel):
    """File info card.

    :param unique_id: Unique Id for the file.
    :type unique_id: str
    :param file_type: Type of file.
    :type file_type: str
    :param etag: ETag for the file.
    :type etag: str | None
    """

    unique_id: str
    file_type: str
    etag: str | None
