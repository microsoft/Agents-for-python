# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Protocol

from microsoft_agents.testing.core import Transcript

class TranscriptFormatter(Protocol):
    """Protocol for transcript formatters."""

    def format(self, transcript: Transcript) -> str:
        """Format the given Transcript into a string representation."""
        raise NotImplementedError


class BaseTranscriptFormatter:
    """Base class for transcript formatters.

    Provides ``__call__`` so formatters can be used as ``Formatter()(transcript)``
    in addition to the explicit ``formatter.format(transcript)`` style.
    """

    def __call__(self, transcript: Transcript) -> str:
        return self.format(transcript)

    def format(self, transcript: Transcript) -> str:
        raise NotImplementedError