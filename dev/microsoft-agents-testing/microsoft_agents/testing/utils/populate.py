# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import Activity


def update_with_defaults(original: dict, defaults: dict) -> None:
    """Populate a dictionary with default values.

    :param original: The original dictionary to populate.
    :param defaults: The dictionary containing default values.
    """

    for key in defaults.keys():
        if key not in original:
            original[key] = defaults[key]
        elif isinstance(original[key], dict) and isinstance(defaults[key], dict):
            update_with_defaults(original[key], defaults[key])


def populate_activity(original: Activity, defaults: Activity | dict) -> Activity:
    """Populate an Activity object with default values.

    :param original: The original Activity object to populate.
    :param defaults: The Activity object or dictionary containing default values.
    """

    if isinstance(defaults, Activity):
        defaults = defaults.model_dump(exclude_unset=True)

    new_activity_dict = original.model_dump(exclude_unset=True)

    for key in defaults.keys():
        if key not in new_activity_dict:
            new_activity_dict[key] = defaults[key]

    return Activity.model_validate(new_activity_dict)
