# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from microsoft_agents.hosting.dialogs import DialogSet, ComponentDialog, WaterfallDialog
from microsoft_agents.hosting.core import ConversationState, MemoryStorage
from microsoft_agents.hosting.dialogs._telemetry_client import NullTelemetryClient


class MyBotTelemetryClient(NullTelemetryClient):
    def __init__(self):
        super().__init__()


class TestDialogSet:
    def test_dialogset_constructor_valid(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state_property = convo_state.create_property("dialogstate")
        dialog_set = DialogSet(dialog_state_property)
        assert dialog_set is not None

    def test_dialogset_constructor_null_property(self):
        with pytest.raises(TypeError):
            DialogSet(None)

    def test_dialogset_constructor_null_from_componentdialog(self):
        ComponentDialog("MyId")

    def test_dialogset_telemetryset(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state_property = convo_state.create_property("dialogstate")
        dialog_set = DialogSet(dialog_state_property)

        dialog_set.add(WaterfallDialog("A"))
        dialog_set.add(WaterfallDialog("B"))

        assert isinstance(
            dialog_set.find_dialog("A").telemetry_client, NullTelemetryClient
        )
        assert isinstance(
            dialog_set.find_dialog("B").telemetry_client, NullTelemetryClient
        )

        dialog_set.telemetry_client = MyBotTelemetryClient()

        assert isinstance(
            dialog_set.find_dialog("A").telemetry_client, MyBotTelemetryClient
        )
        assert isinstance(
            dialog_set.find_dialog("B").telemetry_client, MyBotTelemetryClient
        )

    def test_dialogset_nulltelemetryset(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state_property = convo_state.create_property("dialogstate")
        dialog_set = DialogSet(dialog_state_property)

        dialog_set.add(WaterfallDialog("A"))
        dialog_set.add(WaterfallDialog("B"))

        dialog_set.telemetry_client = MyBotTelemetryClient()
        dialog_set.telemetry_client = None

        assert not isinstance(
            dialog_set.find_dialog("A").telemetry_client, MyBotTelemetryClient
        )
        assert not isinstance(
            dialog_set.find_dialog("B").telemetry_client, MyBotTelemetryClient
        )
        assert isinstance(
            dialog_set.find_dialog("A").telemetry_client, NullTelemetryClient
        )
        assert isinstance(
            dialog_set.find_dialog("B").telemetry_client, NullTelemetryClient
        )
