class TestActivityModel:

    def test_serialize_basic(self, activity):
        activity_copy = Activity(
            **activity.model_dump(mode="json", exclude_unset=True, by_alias=True)
        )
        assert activity_copy == activity