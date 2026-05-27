# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json

from .transcript_formatter import BaseTranscriptFormatter
from .utils import _exchange_sort_key

from microsoft_agents.activity import Activity
from microsoft_agents.testing.core import Transcript

class ActivityTranscriptFormatter(BaseTranscriptFormatter):
    """Formats a transcript as a JSON string."""

    def __init__(self, model_dump_args: dict | None = None):
        self._model_dump_args = model_dump_args or {}
    
    def format(self, transcript: Transcript) -> str:

        exchanges = sorted(transcript.history(), key=_exchange_sort_key)

        activities: list[Activity] = []

        for exchange in exchanges:
            if exchange.request:
                activities.append(exchange.request)
            if exchange.responses:
                activities.extend(exchange.responses)
        
        activity_dicts: list[dict] = [
            activity.model_dump(**self._model_dump_args) for activity in activities
        ]

        return json.dumps(activity_dicts)