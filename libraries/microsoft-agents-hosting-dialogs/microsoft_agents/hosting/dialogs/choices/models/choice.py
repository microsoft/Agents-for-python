# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field

from microsoft_agents.activity import CardAction


@dataclass
class Choice:

    value: str = ""
    action: CardAction | None = None
    synonyms: list[str] = field(default_factory=list)
