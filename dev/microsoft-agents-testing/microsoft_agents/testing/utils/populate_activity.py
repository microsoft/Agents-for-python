from microsoft_agents.activity import Activity


def populate_activity(original: Activity, defaults: Activity | dict) -> Activity:
    """Populate an Activity object with default values."""

    if isinstance(defaults, Activity):
        defaults = defaults.model_dump(exclude_unset=True)

    new_activity = original.model_copy()

    for key in defaults.keys():
        if getattr(new_activity, key) is None:
            setattr(new_activity, key, defaults[key])

    return new_activity