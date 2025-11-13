# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import Activity

def populate(original: dict, defaults: dict) -> None:
    """Populate a dictionary with default values."""

    for key in defaults.keys():
        if key not in original:
            original[key] = defaults[key]
        elif isinstance(original[key], dict) and isinstance(defaults[key], dict):
            populate(original[key], defaults[key])

def populate_activity(original: Activity, defaults: Activity | dict) -> Activity:
    """Populate an Activity object with default values."""

    if isinstance(defaults, Activity):
        defaults = defaults.model_dump(exclude_unset=True)

    new_activity = original.model_copy()

    for key in defaults.keys():
        if getattr(new_activity, key) is None:
            setattr(new_activity, key, defaults[key])

    return new_activity
