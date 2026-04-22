# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field

@dataclass
class UserProfile:

    name: str = ""
    age: int = 0
    companies_to_review: list[str] = field(default_factory=list)
