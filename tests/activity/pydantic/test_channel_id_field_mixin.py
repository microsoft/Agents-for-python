import pytest

from typing import Optional
from pydantic import BaseModel, ValidationError

from microsoft_agents.activity import ChannelId, _ChannelIdFieldMixin


class DummyModel(BaseModel, _ChannelIdFieldMixin): ...


def channel_id_eq(a: Optional[ChannelId], b: Optional[ChannelId]) -> bool:
    return a.channel == b.channel and a.sub_channel == b.sub_channel and a == b


class TestChannelIdFieldMixin:

    def test_validation_basic(self):
        model = DummyModel(channel_id="email:support")
        assert channel_id_eq(model.channel_id, ChannelId("email:support"))
        model = DummyModel(channel_id="email")
        assert channel_id_eq(model.channel_id, ChannelId("email"))
        model = DummyModel(channel_id="channel:sub_channel:extra")
        assert channel_id_eq(model.channel_id, ChannelId("channel:sub_channel:extra"))

    def test_validation_from_channel_id(self):
        model = DummyModel(channel_id=ChannelId("email:support"))
        assert channel_id_eq(model.channel_id, ChannelId("email:support"))

    def test_validation_dict(self):
        model = DummyModel.model_validate({"channelId": "email:support"})
        assert channel_id_eq(model.channel_id, ChannelId("email:support"))

    def test_validation_dict_camel_case(self):
        model = DummyModel.model_validate({"channel_id": "email:support"})
        assert channel_id_eq(model.channel_id, ChannelId("email:support"))

    def test_validation_none(self):
        model = DummyModel.model_validate({})
        assert model.channel_id is None

    def test_validation_invalid_type(self):
        with pytest.raises(ValidationError):
            DummyModel.model_validate({"channelId": 123})
        with pytest.raises(ValidationError):
            DummyModel.model_validate({"channel_id": 123})
        with pytest.raises(ValidationError):
            DummyModel.model_validate({"channelId": None})
        with pytest.raises(ValidationError):
            DummyModel(channel_id=123)

    def test_serialize(self):
        model = DummyModel(channel_id="email:support")
        assert model.model_dump() == {"channel_id": "email:support"}
        assert model.model_dump_json() == '{"channel_id":"email:support"}'
        assert model.model_dump(by_alias=True) == {"channelId": "email:support"}
        assert model.model_dump_json(by_alias=True) == '{"channelId":"email:support"}'
        assert model.model_dump(exclude_unset=True) == {"channel_id": "email:support"}

    def test_serialize_none(self):
        model = DummyModel()
        assert model.model_dump() == {}
        assert model.model_dump_json() == "{}"
        assert model.model_dump(by_alias=True) == {}
        assert model.model_dump_json(by_alias=True) == "{}"
        assert model.model_dump(exclude_unset=True) == {}

    def test_set(self):
        model = DummyModel()
        assert model.channel_id is None
        model.channel_id = "email:support"
        assert channel_id_eq(model.channel_id, ChannelId("email:support"))
        model.channel_id = "a:b:c"
        assert channel_id_eq(model.channel_id, ChannelId("a:b:c"))
        model.channel_id = ChannelId("email")
        assert channel_id_eq(model.channel_id, ChannelId("email"))
        with pytest.raises(Exception):
            model.channel_id = 123
        with pytest.raises(Exception):
            model.channel_id = ""
        with pytest.raises(Exception):
            model.channel_id = None
