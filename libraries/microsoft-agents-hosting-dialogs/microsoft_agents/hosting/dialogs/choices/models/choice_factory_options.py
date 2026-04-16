# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass

@dataclass
class ChoiceFactoryOptions:

    inline_separator: str | None = None
    inline_or: str | None = None
    inline_or_more: str | None = None
    include_numbers: bool = True