from pydantic import BaseModel
from typing import Optional


class FileInfoCard(BaseModel):
    """File info card.

    :param unique_id: Unique Id for the file.
    :type unique_id: str
    :param file_type: Type of file.
    :type file_type: str
    :param etag: ETag for the file.
    :type etag: Optional[str]
    """

    unique_id: str
    file_type: str
    etag: Optional[str]
