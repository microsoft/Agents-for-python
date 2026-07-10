from dataclasses import dataclass

import pytest

from microsoft_agents.hosting.core.app.input_file import InputFile
from microsoft_agents.hosting.core.app.state import TempState


@dataclass
class ExampleValue:
    value: str


def test_temp_state_name_is_scope_name():
    state = TempState()

    assert state.name == "temp"
    assert state.SCOPE_NAME == "temp"


def test_temp_state_get_value_uses_factory_once_and_caches_value():
    state = TempState()
    calls = 0

    def factory():
        nonlocal calls
        calls += 1
        return []

    first_value = state.get_value("items", factory)
    first_value.append("value")
    second_value = state.get_value("items", factory)

    assert calls == 1
    assert second_value == ["value"]
    assert first_value is second_value


def test_temp_state_has_set_and_delete_value():
    state = TempState()

    state.set_value("name", "value")
    assert state.has_value("name")
    assert state.get_value("name") == "value"

    state.delete_value("name")
    assert not state.has_value("name")
    assert state.get_value("name") is None


def test_temp_state_input_files_uses_dedicated_key():
    state = TempState()
    input_files = [
        InputFile(
            content=b"hello",
            content_type="text/plain",
            content_url="https://example.com/file.txt",
        )
    ]

    assert state.input_files == []

    state.input_files = input_files

    assert state.input_files == input_files
    assert state.get_value(TempState.INPUT_FILES_KEY) == input_files


def test_temp_state_typed_values_use_value_type_as_key():
    state = TempState()
    value = ExampleValue("test")

    state.set_typed_value(value)

    assert state.get_typed_value(ExampleValue) is value


def test_temp_state_clear_and_delete_state_remove_all_values():
    state = TempState()
    state.set_value("name", "value")

    state.clear(None)

    assert not state.has_value("name")


@pytest.mark.asyncio
async def test_temp_state_async_methods_are_noops_or_clear_state():
    state = TempState()
    state.set_value("name", "value")

    await state.load(None)
    await state.save(None)
    await state.save_changes(None)

    assert state.has_value("name")
    assert state.is_loaded()

    await state.delete_state(None)

    assert not state.has_value("name")
