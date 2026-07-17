# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .transcript_formatter import BaseTranscriptFormatter
from .utils import _exchange_sort_key

from microsoft_agents.testing.core import Transcript

class JsonTranscriptFormatter(BaseTranscriptFormatter):
    """Formats a transcript as a JSON array of Exchange objects.

    Produces a JSON array where each element is a full Exchange (request + responses
    + metadata).  Use ``ActivityTranscriptFormatter`` instead if you need a flat
    list of individual Activity objects without the exchange structure.

    Args:
        model_dump_args: Keyword arguments forwarded to ``Exchange.model_dump_json``
            (e.g. ``{"exclude_unset": True, "exclude_none": True}``).
    """

    def __init__(self, model_dump_args: dict | None = None):
        self._model_dump_args = model_dump_args or {}

    def format(self, transcript: Transcript) -> str:
        """Return a JSON array string of all exchanges in chronological order."""
        exchanges = sorted(transcript.history(), key=_exchange_sort_key)

        parts = [exchange.model_dump_json(**self._model_dump_args) for exchange in exchanges]
        return "[" + ",".join(parts) + "]"