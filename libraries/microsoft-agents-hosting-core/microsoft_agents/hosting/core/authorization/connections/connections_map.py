# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import Mapping
from dataclasses import dataclass

from microsoft_agents.activity.config import Configuration, xpath


@dataclass(frozen=True)
class _ConnectionMapItem:
    service_url: str = ""
    audience: str = ""
    connection: str = ""


class _ConnectionMap:
    """Ordered connection routing rules bound from lists or named mappings."""

    def __init__(self, items: list | Mapping | None = None):
        if items is None:
            items = []
        if not isinstance(items, (list, Mapping)):
            raise TypeError("Connections map must be a list or mapping.")
        values = items.values() if isinstance(items, Mapping) else items
        self.items: list[_ConnectionMapItem] = []
        for index, value in enumerate(values):
            if not isinstance(value, Mapping):
                raise TypeError(f"Connections map entry {index} must be a mapping.")
            config = Configuration(value)
            self.items.append(
                _ConnectionMapItem(
                    service_url=config.get_str(xpath("service_url"), default=""),
                    audience=config.get_str(xpath("audience"), default=""),
                    connection=config.get_str(xpath("connection"), default=""),
                )
            )

    def __iter__(self):
        return iter(self.items)

    def __bool__(self):
        return bool(self.items)
