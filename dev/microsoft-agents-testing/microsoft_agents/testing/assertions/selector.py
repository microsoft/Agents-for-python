from __future__ import annotations

from enum import Enum

from microsoft_agents.activity import Activity

from .check_activity import check_activity


class SelectorQuantifier(str, Enum):
    """Defines the types of selectors that can be used to select activities."""

    ALL = "ALL"
    ONE = "ONE"


class Selector:
    """Class for selecting activities based on a selector and quantifier."""

    _selector: dict
    _quantifier: SelectorQuantifier
    _index: int | None

    def __init__(
        self,
        selector: dict | Activity | None = None,
        quantifier: SelectorQuantifier | str | None = None,
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

        if not quantifier and index is None:
            raise ValueError("Either quantifier or index must be provided.")

        if selector is None:
            selector = {}
        elif isinstance(selector, Activity):
            selector = selector.model_dump(exclude_unset=True)

        # make sure quantifier is of type SelectorQuantifier
        if quantifier and isinstance(quantifier, str):
            quantifier_name = quantifier.upper()
            if quantifier_name not in SelectorQuantifier.__members__:
                raise ValueError(f"Invalid quantifier: {quantifier_name}")
            quantifier = SelectorQuantifier(quantifier_name)

        # validate index and quantifier combination
        if index is None:
            if quantifier == SelectorQuantifier.ONE:
                index = 0
            elif quantifier not in SelectorQuantifier:
                raise ValueError(f"Invalid quantifier: {quantifier}")
        else:
            if quantifier == SelectorQuantifier.ALL:
                raise ValueError("Index should not be set when quantifier is ALL.")
            quantifier = SelectorQuantifier.ONE

        assert isinstance(quantifier, SelectorQuantifier)  # linter hint

        self._quantifier = quantifier
        self._index = index
        self._selector = selector

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
        if self._quantifier == SelectorQuantifier.ALL:
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

            assert self._index is not None  # linter hint
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
        selector = config.get("selector", {})
        quantifier = config.get("quantifier", None)
        index = config.get("index", None)

        return Selector(
            selector=selector,
            quantifier=quantifier,
            index=index,
        )
