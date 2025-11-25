# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from .check_model import check_model

class ModelSelector:
    """Class for selecting activities based on a model and an index."""

    _model: dict
    _index: int | None

    def __init__(
        self,
        model: dict | None = None,
        index: int | None = None,
    ) -> None:
        """Initializes the ModelSelector with the given configuration.

        :param model: The model to use for selecting activities.
            The model is an object holding the fields to match and assertions to pass.
        :param index: The index of the item to select when quantifier is ONE.
        """

        if model is None:
            model = {}

        self._model = model
        self._index = index

    def select_first(self, items: list[dict]) -> dict | None:
        """Selects the first item from the list of items.

        :param items: The list of items to select from.
        :return: The first item, or None if no items exist.
        """
        res = self.select(items)
        if res:
            return res[0]
        return None

    def select(self, items: list[dict]) -> list[dict]:
        """Selects items based on the selector configuration.

        :param items: The list of items to select from.
        :return: A list of selected items.
        """
        if self._index is None:
            return list(
                filter(
                    lambda item: check_model(item, self._model),
                    items,
                )
            )
        else:
            filtered_list = []
            for item in items:
                if check_model(item, self._model):
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
    def from_config(config: dict) -> ModelSelector:
        """Creates a ModelSelector instance from a configuration dictionary.

        :param config: The configuration dictionary containing selector, and index.
        :return: A Selector instance.
        """
        model = config.get("model", {})
        index = config.get("index", None)

        return ModelSelector(
            model=model,
            index=index,
        )
