"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import pytest

from microsoft_agents.activity import ConversationParameters
from microsoft_agents.hosting.core.app.proactive import CreateConversationOptions
from microsoft_agents.hosting.core.authorization import ClaimsIdentity


def _make_identity():
    return ClaimsIdentity(claims={"aud": "app-id"}, is_authenticated=True)


def _make_params():
    return ConversationParameters()


class TestCreateConversationOptionsDefaults:
    def test_default_identity_is_none(self):
        opts = CreateConversationOptions()
        assert opts.identity is None

    def test_default_channel_id_is_empty(self):
        opts = CreateConversationOptions()
        assert opts.channel_id == ""

    def test_default_parameters_is_none(self):
        opts = CreateConversationOptions()
        assert opts.parameters is None

    def test_default_service_url_is_none(self):
        opts = CreateConversationOptions()
        assert opts.service_url is None

    def test_default_audience_is_none(self):
        opts = CreateConversationOptions()
        assert opts.audience is None

    def test_default_store_conversation_is_false(self):
        opts = CreateConversationOptions()
        assert opts.store_conversation is False


class TestCreateConversationOptionsAssignment:
    def test_identity_assigned(self):
        identity = _make_identity()
        opts = CreateConversationOptions(identity=identity)
        assert opts.identity is identity

    def test_channel_id_assigned(self):
        opts = CreateConversationOptions(channel_id="msteams")
        assert opts.channel_id == "msteams"

    def test_parameters_assigned(self):
        params = _make_params()
        opts = CreateConversationOptions(parameters=params)
        assert opts.parameters is params

    def test_service_url_assigned(self):
        opts = CreateConversationOptions(service_url="https://custom/")
        assert opts.service_url == "https://custom/"

    def test_audience_assigned(self):
        opts = CreateConversationOptions(audience="https://api.botframework.com")
        assert opts.audience == "https://api.botframework.com"

    def test_store_conversation_assigned(self):
        opts = CreateConversationOptions(store_conversation=True)
        assert opts.store_conversation is True


class TestCreateConversationOptionsValidate:
    def test_validate_passes_with_required_fields(self):
        opts = CreateConversationOptions(
            identity=_make_identity(),
            channel_id="msteams",
            parameters=_make_params(),
            service_url="https://custom/",
        )
        opts.validate()  # must not raise

    def test_validate_optional_fields_not_required(self):
        opts = CreateConversationOptions(
            identity=_make_identity(),
            channel_id="msteams",
            parameters=_make_params(),
            service_url="https://custom/",
            audience=None,
        )
        opts.validate()  # must not raise

    def test_validate_raises_when_identity_missing(self):
        opts = CreateConversationOptions(channel_id="msteams", parameters=_make_params())
        with pytest.raises(ValueError, match="identity"):
            opts.validate()

    def test_validate_raises_when_channel_id_empty(self):
        opts = CreateConversationOptions(
            identity=_make_identity(), parameters=_make_params()
        )
        with pytest.raises(ValueError, match="channel_id"):
            opts.validate()

    def test_validate_raises_when_parameters_missing(self):
        opts = CreateConversationOptions(
            identity=_make_identity(), channel_id="msteams"
        )
        with pytest.raises(ValueError, match="parameters"):
            opts.validate()

    def test_validate_raises_when_all_missing(self):
        opts = CreateConversationOptions()
        with pytest.raises(ValueError):
            opts.validate()
