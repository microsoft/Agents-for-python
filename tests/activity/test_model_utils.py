import pytest
from pydantic import ValidationError

from microsoft_agents.activity import Activity, AgentsModel, ChannelAccount
from microsoft_agents.activity._model_utils import (
    ModelFieldHelper,
    SkipIf,
    SkipNone,
    pick_model,
    pick_model_dict,
)

from tests.activity._common.model_utils import PickField, SkipEmpty, SkipFalse


class ExampleModel(AgentsModel):
    model_value: str | None = None
    count: int | None = None


class RenameField(ModelFieldHelper):
    def __init__(self, value, target_key: str):
        self.value = value
        self.target_key = target_key

    def process(self, key: str):
        return {self.target_key: self.value}


class DropField(ModelFieldHelper):
    def process(self, key: str):
        return {}


def test_model_field_helper_process_must_be_implemented():
    with pytest.raises(NotImplementedError):
        ModelFieldHelper().process("field")


def test_skip_if_skips_value_when_condition_is_true():
    field = SkipIf("secret", lambda value: value == "secret")

    assert field.process("field") == {}


def test_skip_if_includes_value_when_condition_is_false():
    field = SkipIf("", lambda value: value is None)

    assert field.process("field") == {"field": ""}


@pytest.mark.parametrize("value", [0, False, "", [], {}])
def test_skip_none_includes_falsy_values_that_are_not_none(value):
    field = SkipNone(value)

    assert field.process("field") == {"field": value}


def test_skip_none_skips_none():
    field = SkipNone(None)

    assert field.process("field") == {}


@pytest.mark.parametrize("value", [0, None, [], {}, False, ""])
def test_skip_false_skips_falsy_values(value):
    field = SkipFalse(value)

    assert field.process("field") == {}


@pytest.mark.parametrize("value", [2, [1, 2, 3], "aha"])
def test_skip_false_includes_truthy_values(value):
    field = SkipFalse(value)

    assert field.process("field") == {"field": value}


@pytest.mark.parametrize("value", ["", [], set(), {}, tuple()])
def test_skip_empty_skips_empty_values(value):
    field = SkipEmpty(value)

    assert field.process("field") == {}


@pytest.mark.parametrize("value", ["wow", [2], set("a"), {"a": "b"}])
def test_skip_empty_includes_nonempty_values(value):
    field = SkipEmpty(value)

    assert field.process("field") == {"field": value}


def test_pick_model_dict_processes_helpers_and_keeps_plain_values():
    result = pick_model_dict(
        plain="value",
        keep_none=None,
        overwrite="initial-value",
        skipped=DropField(),
        renamed=RenameField("renamed-value", "target"),
        optional=SkipNone(None),
        present=SkipNone("present-value"),
        skipped_condition=SkipIf(
            "skipped-value", lambda value: value == "skipped-value"
        ),
        overwrite_helper=RenameField("overwritten-value", "overwrite"),
    )

    assert result == {
        "plain": "value",
        "keep_none": None,
        "target": "renamed-value",
        "present": "present-value",
        "overwrite": "overwritten-value",
    }


def test_pick_model_creates_model_from_processed_fields():
    model = pick_model(
        ExampleModel,
        model_value=SkipNone("test-value"),
        count=SkipNone(None),
    )

    assert model == ExampleModel(model_value="test-value")
    assert "model_value" in model.model_fields_set
    assert "count" not in model.model_fields_set


def test_pick_model_supports_nested_models_and_preserves_unset_fields():
    recipient = ChannelAccount(id="123", name="foo")

    activity = pick_model(
        Activity,
        type="message",
        id=SkipNone(None),
        from_property=pick_model(
            ChannelAccount,
            id=PickField(recipient),
            aad_object_id=PickField(recipient),
        ),
        recipient=pick_model(
            ChannelAccount,
            id=PickField(recipient),
            name=PickField(recipient),
            role=PickField(recipient),
        ),
        text=PickField(recipient, "name"),
    )

    assert activity == Activity(
        type="message",
        from_property=ChannelAccount(id="123"),
        recipient=ChannelAccount(id="123", name="foo"),
        text="foo",
    )
    assert "id" not in activity.model_fields_set
    assert "aad_object_id" not in activity.from_property.model_fields_set
    assert "role" not in activity.recipient.model_fields_set
    assert "text" in activity.model_fields_set


def test_pick_model_uses_model_validation():
    with pytest.raises(ValidationError):
        pick_model(ExampleModel, count="not-an-int")
