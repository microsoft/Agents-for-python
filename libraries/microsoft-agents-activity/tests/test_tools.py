import pytest

from microsoft_agents.activity import Activity, ChannelAccount
from microsoft_agents.activity._model_utils import (
    ModelFieldHelper,
    SkipNone,
    SkipIf,
    pick_model,
    pick_model_dict,
)

from .activity_tools.testing_model_utils import SkipFalse, SkipEmpty, PickField


class TestModelUtils:

    def test_skip_if(self):
        field = SkipIf("foo", lambda v: v == "foo")
        assert field.process("key") == {}

    @pytest.mark.parametrize(
        "value, expected",
        [
            [None, {}],
            [42, {"field": 42}],
            ["foo", {"field": "foo"}],
        ],
    )
    def test_skip_none(self, value, expected):
        field = SkipNone(value)
        assert field.process("field") == expected

    @pytest.mark.parametrize("value", [0, None, [], {}, False, ""])
    def test_skip_false_with_falsy_value(self, value):
        field = SkipFalse(value)
        assert field.process("key") == {}

    @pytest.mark.parametrize("value", [2, [1, 2, 3], "aha"])
    def test_skip_false_with_truthy_value(self, value):
        field = SkipFalse(value)
        assert field.process("key") == {"key": value}

    @pytest.mark.parametrize("value", ["", [], set(), {}, tuple()])
    def test_skip_empty_with_empty_value(self, value):
        field = SkipEmpty(value)
        assert field.process("key") == {}

    @pytest.mark.parametrize("value", ["wow", [2], set("a"), {"a": "b"}])
    def test_skip_empty_with_nonempty_value(self, value):
        field = SkipEmpty(value)
        assert field.process("key") == {"key": value}

    def test_pick_model(self, mocker):
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
        expected = Activity(
            type="message",
            from_property=ChannelAccount(id="123"),
            recipient=ChannelAccount(id="123", name="foo"),
            text="foo",
        )

        assert activity == expected
        assert "id" not in activity.model_fields_set
        assert "aad_object_id" not in activity.from_property.model_fields_set
        assert "role" not in activity.recipient.model_fields_set
        assert "text" in activity.model_fields_set

    def test_pick_model_dict(self):
        class Foo(ModelFieldHelper):
            def process(self, key):
                return {key: "bar"}

        class Bar(ModelFieldHelper):
            def process(self, key):
                return {"bar": "bar"}

        foo = Foo()
        result = foo.process("foo")
        assert result == {"foo": "bar"}

        res = pick_model_dict(
            a=Foo(),
            b=SkipNone("bar"),
            c=SkipIf("baz", lambda v: v == "baz"),
            d=Foo(),
            e=None,
            f=42,
            bar=7,
            g=Bar(),
        )

        assert res == {
            "a": "bar",
            "b": "bar",
            "d": "bar",
            "e": None,
            "f": 42,
            "bar": "bar",
        }
