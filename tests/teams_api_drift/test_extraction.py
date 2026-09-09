# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import enum
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel, Field, ConfigDict, Discriminator

from teams_api_drift.extract import model_for, type_name


class Parent(BaseModel):
    name: str = Field(alias="displayName")


class Child(Parent):
    optional: str | None = None
    status: Literal["open", "closed"] = "open"
    model_config = ConfigDict(populate_by_name=True)


def test_pydantic_inheritance_aliases_defaults_and_config_are_extracted():
    model = model_for(Child, "Child")
    assert model["properties"]["name"]["alias"] == "displayName"
    assert model["properties"]["name"]["optional"] is False
    assert model["properties"]["optional"]["optional"] is True
    assert model["properties"]["status"]["default"] == "open"
    assert model["modelConfig"]["populate_by_name"] is True


def test_union_representation_is_order_independent():
    assert type_name(str | int | None) == type_name(None | int | str)


def test_annotated_callable_metadata_does_not_include_process_addresses():
    def make_discriminator():
        def discriminator(value):
            return "test"

        return discriminator

    first = Annotated[str, Discriminator(make_discriminator())]
    second = Annotated[str, Discriminator(make_discriminator())]
    assert type_name(first) == type_name(second)
    assert "0x" not in type_name(first)
    assert type_name(Literal["None"]) != type_name(Literal[None])


@pytest.mark.skipif(sys.version_info < (3, 11), reason="Upstream requires Python 3.11")
def test_functions_include_keyword_only_parameters_and_async_contract():
    async def method(value: str, *, count: int = 1) -> bool:
        return True

    signature = model_for(method, "method")["methods"]["$call"][0]
    assert signature["parameters"][1]["kind"] == "KEYWORD_ONLY"
    assert signature["parameters"][1]["optional"] is True
    assert signature["returnType"] == "bool"
    assert signature["async"] is True


class FakeBaseClient:
    @property
    def url(self) -> str:
        return "https://example.com"


class FakeClient(FakeBaseClient):
    def __init__(self, service_url: str):
        self.service_url = service_url.rstrip("/")


@pytest.mark.skipif(sys.version_info < (3, 11), reason="Upstream requires Python 3.11")
def test_constructor_ast_and_inherited_properties(monkeypatch):
    monkeypatch.setattr(FakeBaseClient, "__module__", "microsoft_teams.api.fixture")
    monkeypatch.setattr(FakeClient, "__module__", "microsoft_teams.api.fixture")
    result = model_for(FakeClient, "Client")
    assert result["properties"]["service_url"]["type"] == "str"
    assert result["properties"]["url"]["type"] == "str"
    assert result["properties"]["url"]["writable"] is False
    assert result["constructors"][0]["parameters"][0]["name"] == "service_url"


def test_enum_values_are_part_of_the_api_model():
    class Status(enum.Enum):
        READY = "ready"

    assert model_for(Status, "Status")["enumMembers"] == {"READY": "ready"}


@pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695 needs Python 3.12")
def test_pep695_alias_retains_underlying_type():
    namespace = {}
    exec("type Message = str | None", namespace)
    assert type_name(namespace["Message"]) == "None | str"
