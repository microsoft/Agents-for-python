from .check import Check

class ActivityAssert:

    def __init__(self, activities: list[Activity]) -> None:
        self._activities = activities

    def has_attachments(self) -> Check:
        return Check(
            any(activity.attachments for activity in self._activities),
            "Expected at least one activity to have attachments, but none did."
        )