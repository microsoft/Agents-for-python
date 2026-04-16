# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass

@dataclass
class FoundValue:
    """Represents a result from matching user input against a list of choices
    
    
    value: The value that was matched.
    index: The index of the value that was matched.
    score: The accuracy with which the synonym matched the specified portion of the utterance.
    A value of 1.0 would indicate a perfect match.
    """

    value: str
    index: int
    score: float