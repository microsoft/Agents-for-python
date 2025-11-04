import json

from microsoft_agents.activity import Activity

def load_activity(channel: str, name: str) -> Activity:

    with open("./dev/integration/src/tests/integration/foundational/activities/{}/{}.json".format(channel, name), "r") as f:
        activity = json.load(f)

    return Activity.model_validate(activity)