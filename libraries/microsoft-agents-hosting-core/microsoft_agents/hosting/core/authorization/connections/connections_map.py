# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass, field

from microsoft_agents.activity.config import _Confiurableg

@dataclass(frozen=True)
class _ConnectionMapItem():

    service_url: str = ""
    audience: str = ""
    connection: str = ""

@dataclass(frozen=True)
class _ConnectionMap(_Configurable):
    items: list[_ConnectionMapItem] = field(default_factory=list)

    def __init__(self, items: list[_ConnectionMapItem] | list[dict] | dict[str, dict] | None = None) -> None:
        """Initialize a _ConnectionMap with a list of _ConnectionMapItem, a list of dicts, or a dict of dicts."""

        final_items: list[_ConnectionMapItem] = []

        if items is None:
            final_items = []
        else:
            item_iter = items.items() if isinstance(items, dict) else enumerate(items)
            for key, val in item_iter:
                if isinstance(val, _ConnectionMapItem):
                    final_items.append(val)
                    continue
                if not isinstance(val, dict):
                    raise ValueError(f"Expected dict for key '{key}', got {type(val).__name__}")
                final_items.append(_ConnectionMapItem(**val))

        object.__setattr__(self, "items", final_items)

    def __getitem__(self, index: str) -> _ConnectionMapItem:
        for item in self.items:
            if item.connection == index:
                return item
        raise KeyError(f"No connection map item found for connection '{index}'")

    def __iter__(self):
        return iter(self.items)