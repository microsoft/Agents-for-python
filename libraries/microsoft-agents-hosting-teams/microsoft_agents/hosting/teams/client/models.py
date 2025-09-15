from typing import Optional
from pydantic import BaseModel

from ..activity_extensions.teams_channel_account import TeamsChannelAccount

class TeamDetails(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    add_group_id: Optional[str] = None
    channel_count: Optional[int] = None
    member_count: Optional[int] = None
    type: Optional[str] = None

class TeamsMember(BaseModel):
    id: str

class TeamsPagedMembersResult(BaseModel):
    continuation_token: str
    members: list[TeamsChannelAccount]

class BatchFailedEntry(BaseModel):
    id: str
    error: str

class BatchFailedEntriesResponse(BaseModel):
    continuation_token: str
    failed_entry_response: list[BatchFailedEntry]

class BatchOperationsStateResponse:
    state: str
    status_map: dict[int, int]
    total_entries_count: int
    retry_after: Optional[float] = None # robrandao: TODO -> wrong type?

class CancelOperationResponse(BaseModel):
    pass

class ResourceResponse(BaseModel):
    id: str

class TeamsBatchOperationResponse(BatchOperationResponse):
    pass