# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from .check_model import check_model


class Selector:
    """Class for selecting activities based on a selector and quantifier."""

    _selector: dict
    _index: int | None

    def __init__(
        self,
        selector: dict | None = None,
        index: int | None = None,
    ) -> None:
        """Initializes the Selector with the given configuration.

        :param selector: The selector to use for selecting activities.
            The selector is an object holding the activity fields to match.
        :param quantifier: The quantifier to use for selecting activities.
        :param index: The index of the activity to select when quantifier is ONE.

        When quantifier is ALL, index should be None.
        When quantifier is ONE, index defaults to 0 if not provided.
        """

        if selector is None:
            selector = {}

        self._selector = selector
        self._index = index

    def select_first(self, items: list[dict]) -> dict | None:
        """Selects the first activity from the list of activities.

        :param items: The list of items to select from.
        :return: A list containing the first item, or an empty list if none exist.
        """
        res = self.select(items)
        if res:
            return res[0]
        return None

    def select(self, items: list[dict]) -> list[dict]:
        """Selects activities based on the selector configuration.

        :param items: The list of items to select from.
        :return: A list of selected items.
        """
        if self._index is None:
            return list(
                filter(
                    lambda item: check_model(item, self._selector),
                    items,
                )
            )
        else:
            filtered_list = []
            for item in items:
                if check_model(item, self._selector):
                    filtered_list.append(item)

            if self._index < 0 and abs(self._index) <= len(filtered_list):
                return [filtered_list[self._index]]
            elif self._index >= 0 and self._index < len(filtered_list):
                return [filtered_list[self._index]]
            else:
                return []

    def __call__(self, items: list[dict]) -> list[dict]:
        """Allows the Selector instance to be called as a function.

        :param items: The list of items to select from.
        :return: A list of selected items.
        """
        return self.select(items)

    @staticmethod
    def from_config(config: dict) -> Selector:
        """Creates a Selector instance from a configuration dictionary.

        :param config: The configuration dictionary containing selector, quantifier, and index.
        :return: A Selector instance.
        """
        selector = config.get("selector", {})
        index = config.get("index", None)

        return Selector(
            selector=selector,
            index=index,
        )
