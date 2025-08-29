import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTreatment,
    ActivityTreatmentType,
    Entity,
    EntityTypes,
    Mention,
)


class TestActivityGetEntities:

    @pytest.fixture
    def activity(self):
        return Activity(
            type="message",
            entities=[
                ActivityTreatment(treatment=ActivityTreatmentType.TARGETED),
                Entity(
                    type=EntityTypes.ACTIVITY_TREATMENT,
                    treatment=ActivityTreatmentType.TARGETED,
                ),
                Mention(type=EntityTypes.MENTION, text="Hello"),
                Entity(type=EntityTypes.MENTION),
                Entity(type=EntityTypes.ACTIVITY_TREATMENT, treatment=None),
            ],
        )

    def test_activity_get_mentions(self, activity):
        expected = [
            Mention(type=EntityTypes.MENTION, text="Hello"),
            Entity(type=EntityTypes.MENTION),
        ]
        ret = activity.get_mentions()
        assert activity.get_mentions() == expected
        assert ret[0].text == "Hello"
        assert ret[0].type == EntityTypes.MENTION
        assert not hasattr(ret[1], "text")
        assert ret[1].type == EntityTypes.MENTION

    def test_activity_get_activity_treatments(self, activity):
        expected = [
            ActivityTreatment(treatment=ActivityTreatmentType.TARGETED),
            Entity(
                type=EntityTypes.ACTIVITY_TREATMENT,
                treatment=ActivityTreatmentType.TARGETED,
            ),
            Entity(type=EntityTypes.ACTIVITY_TREATMENT, treatment=None),
        ]
        ret = activity.get_activity_treatments()
        assert ret == expected
        assert ret[0].treatment == ActivityTreatmentType.TARGETED
        assert ret[0].type == EntityTypes.ACTIVITY_TREATMENT
        assert ret[1].treatment == ActivityTreatmentType.TARGETED
        assert ret[1].type == EntityTypes.ACTIVITY_TREATMENT
        assert ret[2].treatment is None
        assert ret[2].type == EntityTypes.ACTIVITY_TREATMENT
