import json

from .transcript_formatter import BaseTranscriptFormatter
from .utils import _exchange_sort_key

from microsoft_agents.testing.core import Transcript

class JsonTranscriptFormatter(BaseTranscriptFormatter):
    """Formats a transcript as a JSON string."""

    def __init__(self, model_dump_args: dict | None = None):
        self._model_dump_args = model_dump_args or {}
    
    def format(self, transcript: Transcript) -> str:

        exchanges = sorted(transcript.history(), key=_exchange_sort_key)

        exchange_dicts: list[dict] = [
            exchange.model_dump(**self._model_dump_args) for exchange in exchanges
        ]

        return json.dumps(exchange_dicts)