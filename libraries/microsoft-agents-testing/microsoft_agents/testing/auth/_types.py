# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, eq=False)
class UserTokenKey:
    """A key that uniquely identifies a user token in the mock client."""

    connection_name: str
    user_id: str
    channel_id: str

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, UserTokenKey)
            and self.connection_name.casefold() == other.connection_name.casefold()
            and self.user_id.casefold() == other.user_id.casefold()
            and self.channel_id.casefold() == other.channel_id.casefold()
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.connection_name.casefold(),
                self.user_id.casefold(),
                self.channel_id.casefold(),
            )
        )


@dataclass(frozen=True, eq=False)
class ExchangeableTokenKey(UserTokenKey):
    """A key that uniquely identifies an exchangeable token in the mock client."""

    exchangeable_item: str

    def __eq__(self, other):
        return (
            super().__eq__(other)
            and isinstance(other, ExchangeableTokenKey)
            and self.exchangeable_item.casefold() == other.exchangeable_item.casefold()
        )

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.exchangeable_item.casefold()))


@dataclass(frozen=True)
class TokenMagicCode:
    """A class that represents a magic code for a token."""

    key: UserTokenKey
    magic_code: str
    user_token: str
