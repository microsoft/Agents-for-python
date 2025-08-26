import pytest

from microsoft.agents.activity import (
    Entity,
    EntityTypes,
    Mention,
    ActivityTreatment,
    ActivityTreatmentType,
    ChannelAccount,
)


class TestSerialization:

    def test_mention_serializer(self):
        initial_mention = Mention(text="Hello", mentioned=ChannelAccount(id="abc"))
        initial_mention_dict = initial_mention.model_dump(
            mode="json", exclude_unset=True, by_alias=True
        )
        mention = Mention.model_validate(initial_mention_dict)

        assert initial_mention_dict == {
            "text": "Hello",
            "mentioned": {"id": "abc"},
            "type": EntityTypes.MENTION,
        }
        assert mention == initial_mention

    def test_mention_serializer_as_entity(self):
        initial_mention = Entity(
            text="Hello", mentioned=ChannelAccount(id="abc"), type=EntityTypes.MENTION
        )
        initial_mention_dict = initial_mention.model_dump(
            mode="json", exclude_unset=True, by_alias=True
        )
        mention = Mention.model_validate(initial_mention_dict)

        assert initial_mention_dict == {
            "text": "Hello",
            "mentioned": {"id": "abc"},
            "type": EntityTypes.MENTION,
        }
        assert mention.type == initial_mention.type
        assert mention.text == initial_mention.text
        assert mention.mentioned == initial_mention.mentioned

    def test_activity_treatment_serializer(self):
        initial_treatment = ActivityTreatment(treatment=ActivityTreatmentType.TARGETED)
        initial_treatment_dict = initial_treatment.model_dump(
            mode="json", exclude_unset=True, by_alias=True
        )
        treatment = ActivityTreatment.model_validate(initial_treatment_dict)

        assert initial_treatment_dict == {
            "treatment": ActivityTreatmentType.TARGETED,
            "type": EntityTypes.ACTIVITY_TREATMENT,
        }
        assert treatment == initial_treatment

    def test_activity_treatment_serializer_as_entity(self):
        initial_treatment = Entity(
            treatment=ActivityTreatmentType.TARGETED,
            type=EntityTypes.ACTIVITY_TREATMENT,
        )
        initial_treatment_dict = initial_treatment.model_dump(
            mode="json", exclude_unset=True, by_alias=True
        )
        treatment = ActivityTreatment.model_validate(initial_treatment_dict)

        assert initial_treatment_dict == {
            "treatment": ActivityTreatmentType.TARGETED,
            "type": EntityTypes.ACTIVITY_TREATMENT,
        }
        assert treatment.type == initial_treatment.type
        assert treatment.treatment == initial_treatment.treatment
