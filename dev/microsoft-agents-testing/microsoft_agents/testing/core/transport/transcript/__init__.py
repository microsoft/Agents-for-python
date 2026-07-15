# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Transcript and Exchange - Recording of agent interactions.

Provides classes for capturing and organizing the sequence of
request-response exchanges during agent testing.
"""

from .exchange import Exchange
from .transcript import Transcript

__all__ = [
    "Exchange",
    "Transcript",
]