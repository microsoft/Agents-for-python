# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass


@dataclass
class FoundChoice:
    """Represents a result from matching user input against a list of choices.


    value: The value of the choice that was matched.
    index: The index of the choice that was matched.
    score: The accuracy with which the synonym matched the specified portion of the utterance.
    A value of 1.0 would indicate a perfect match.
    synonym: The synonym that was matched in case of a synonym match.
    """

    value: str
    index: int
    score: float
    synonym: str | None = None
