# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

@dataclass
class TranscriptInfo:
    channel_id : str = ""
    conversation_id : str = ""
    created_on : datetime = datetime.min        
