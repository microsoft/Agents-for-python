# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass

@dataclass
class Token:
    """Represents an individual token, such as a word in an input string.

    start: The index of the first character of the token within the outer input string.
    end: The index of the last character of the token within the outer input string.
    text: The original text of the token.
    normalized: A normalized version of the token. This can include things like lower casing or stemming.
    """

    start: int
    end: int
    text: str
    normalized: str | None