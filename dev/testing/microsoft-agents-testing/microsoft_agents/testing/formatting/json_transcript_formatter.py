# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .transcript_formatter import BaseTranscriptFormatter
from .utils import _exchange_sort_key

from microsoft_agents.testing.core import Transcript

class JsonTranscriptFormatter(BaseTranscriptFormatter):
    """Formats a transcript as a JSON string."""

    def __init__(self, model_dump_args: dict | None = None):
        self._model_dump_args = model_dump_args or {}
    
    def format(self, transcript: Transcript) -> str:

        exchanges = sorted(transcript.history(), key=_exchange_sort_key)

        parts = [exchange.model_dump_json(**self._model_dump_args) for exchange in exchanges]
        return "[" + ",".join(parts) + "]"