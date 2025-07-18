# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional


class FileDownloadInfo(AgentsModel):
    """File download info attachment.

    :param download_url: File download url.
    :type download_url: str
    :param unique_id: Unique Id for the file.
    :type unique_id: str
    :param file_type: Type of file.
    :type file_type: str
    :param etag: ETag for the file.
    :type etag: Optional[str]
    """

    download_url: str
    unique_id: str
    file_type: str
    etag: Optional[str]
