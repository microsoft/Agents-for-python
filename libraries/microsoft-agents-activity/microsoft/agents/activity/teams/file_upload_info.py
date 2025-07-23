# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class FileUploadInfo(AgentsModel):
    """Information about the file to be uploaded.

    :param name: Name of the file.
    :type name: str
    :param upload_url: URL to an upload session that the bot can use to set the file contents.
    :type upload_url: str
    :param content_url: URL to file.
    :type content_url: str
    :param unique_id: ID that uniquely identifies the file.
    :type unique_id: str
    :param file_type: Type of the file.
    :type file_type: str
    """

    name: str
    upload_url: str
    content_url: str
    unique_id: str
    file_type: str
