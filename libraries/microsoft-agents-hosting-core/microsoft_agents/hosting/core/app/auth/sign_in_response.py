from typing import Optional
from dataclasses import dataclass

from ...oauth import FlowStateTag

@dataclass
class SignInResponse:
    token: Optional[str] = None
    tag: FlowStateTag = FlowStateTag.FAILURE