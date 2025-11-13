from typing import Optional

from microsoft_agents.activity import Activity

from .check_activity import check_activity
from .type_defs import SelectorQuantifier


def select_activity(
    activities: list[Activity],
    selector: Activity,
    index: int = 0,
) -> Optional[Activity]:
    """Selects a single activity from a list based on the provided selector and index.

    :param activities: List of activities to select from.
    :param selector: Activity used as a selector.
    :param index: Index of the activity to select when multiple match.
    :return: The selected activity or None if no activity matches.
    """
    res = select_activities(
        activities,
        {"selector": selector, "quantifier": SelectorQuantifier.ONE, "index": index},
    )
    return res[index] if res else None


def select_activities(
    activities: list[Activity], selector_config: dict
) -> list[Activity]:
    """Selects activities from a list based on the provided selector configuration.

    :param activities: List of activities to select from.
    :param selector_config: Configuration dict containing 'selector', 'quantifier', and optionally '
    :return: List of selected activities.
    """

    selector = selector_config.get("selector", {})

    index = selector_config.get("index", None)
    if index is not None:
        quantifier_name = selector_config.get("quantifier", SelectorQuantifier.ONE)
    else:
        quantifier_name = selector_config.get("quantifier", SelectorQuantifier.ALL)
    quantifier_name = quantifier_name.upper()

    if quantifier_name not in SelectorQuantifier.__members__:
        raise ValueError(f"Invalid quantifier: {quantifier_name}")

    quantifier = SelectorQuantifier(quantifier_name)

    if quantifier == SelectorQuantifier.ALL:
        return list(filter(lambda a: check_activity(a, selector), activities))
    else:
        first = next(filter(lambda a: check_activity(a, selector), activities), None)
        return [first] if first is not None else []
