from typing import Optional, TypeVar, Literal, Any

from microsoft_agents.activity import AgentsModel

from .file_upload_info import FileUploadInfo

Action = TypeVar("Action", Literal["accept"], Literal["decline"])

class FileConsentCardResponse(AgentsModel):
    action: Optional[Action] = None
    context: Optional[Any] = None
    upload_info: Optional[FileUploadInfo] = None