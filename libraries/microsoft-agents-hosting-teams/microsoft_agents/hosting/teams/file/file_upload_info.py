from typing import Optional

from microsoft_agents.activity import AgentsModel

class FileUploadInfo:
    name: Optional[str] = None
    upload_url: Optional[str] = None
    content_url: Optional[str] = None
    unique_id: Optional[str] = None
    file_type: Optional[str] = None