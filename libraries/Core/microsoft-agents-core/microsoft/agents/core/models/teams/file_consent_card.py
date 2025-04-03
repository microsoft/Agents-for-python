from pydantic import BaseModel
from typing import Any


class FileConsentCard(BaseModel):
    """File consent card attachment.

    :param description: File description.
    :type description: str
    :param size_in_bytes: Size of the file to be uploaded in Bytes.
    :type size_in_bytes: int
    :param accept_context: Context sent back to the Bot if user consented to upload.
    :type accept_context: Any
    :param decline_context: Context sent back to the Bot if user declined.
    :type decline_context: Any
    """

    description: str
    size_in_bytes: int
    accept_context: Any
    decline_context: Any
