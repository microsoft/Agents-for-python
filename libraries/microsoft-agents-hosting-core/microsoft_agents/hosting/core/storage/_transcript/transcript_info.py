# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class TranscriptInfo:
    channel_id: str = ""
    conversation_id: str = ""
    created_on: datetime = datetime.min.replace(tzinfo=timezone.utc)
