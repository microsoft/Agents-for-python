# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from microsoft_agents.activity import Activity

from .check_activity import check_activity


class Selector:
    """Class for selecting activities based on a selector and quantifier."""

    _selector: dict
    _index: int | None

    def __init__(
        self,
        selector: dict | Activity | None = None,
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
        elif isinstance(selector, Activity):
            selector = selector.model_dump(exclude_unset=True)

        self._selector = selector
        self._index = index

    def select_first(self, activities: list[Activity]) -> Activity | None:
        """Selects the first activity from the list of activities.

        :param activities: The list of activities to select from.
        :return: A list containing the first activity, or an empty list if none exist.
        """
        res = self.select(activities)
        if res:
            return res[0]
        return None

    def select(self, activities: list[Activity]) -> list[Activity]:
        """Selects activities based on the selector configuration.

        :param activities: The list of activities to select from.
        :return: A list of selected activities.
        """
        if self._index is None:
            return list(
                filter(
                    lambda activity: check_activity(activity, self._selector),
                    activities,
                )
            )
        else:
            filtered_list = []
            for activity in activities:
                if check_activity(activity, self._selector):
                    filtered_list.append(activity)

            if self._index < 0 and abs(self._index) <= len(filtered_list):
                return [filtered_list[self._index]]
            elif self._index >= 0 and self._index < len(filtered_list):
                return [filtered_list[self._index]]
            else:
                return []

    def __call__(self, activities: list[Activity]) -> list[Activity]:
        """Allows the Selector instance to be called as a function.

        :param activities: The list of activities to select from.
        :return: A list of selected activities.
        """
        return self.select(activities)

    @staticmethod
    def from_config(config: dict) -> Selector:
        """Creates a Selector instance from a configuration dictionary.

        :param config: The configuration dictionary containing selector, quantifier, and index.
        :return: A Selector instance.
        """
        selector = config.get("activity", {})
        index = config.get("index", None)

        return Selector(
            selector=selector,
            index=index,
        )
