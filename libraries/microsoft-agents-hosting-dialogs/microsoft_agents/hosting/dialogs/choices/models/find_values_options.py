# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Callable

from .token import Token

@dataclass
class FindValuesOptions:
    """Contains search options, used to control how choices are recognized in a user's utterance.

    allow_partial_matches: (Optional) If `True`, then only some of the tokens in a value need to exist to be considered
    a match. The default value is `False`.

    locale: (Optional) locale/culture code of the utterance. Default is `en-US`.

    max_token_distance: (Optional) maximum tokens allowed between two matched tokens in the utterance. So with
    a max distance of 2 the value "second last" would match the utterance "second from the last"
    but it wouldn't match "Wait a second. That's not the last one is it?".
    The default value is "2".

    tokenizer: (Optional) Tokenizer to use when parsing the utterance and values being recognized.
    """

    allow_partial_matches: bool = False
    locale: str = "en-US"
    max_token_distance: int = 2
    tokenizer: Callable[[str, str | None], list[Token]] | None = None