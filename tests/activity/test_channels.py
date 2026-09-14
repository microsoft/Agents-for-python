import pytest

from microsoft_agents.activity import Channels, ChannelId


def _forms(base: str) -> list:
    """Build equivalent representations of a channel id for a given base channel.

    Returns the plain string, the plain string with a sub-channel, and the
    corresponding ChannelId instances (with and without a sub-channel), plus
    the Channels enum member when one exists for the base value.
    """
    forms = [
        base,
        f"{base}:sub",
        ChannelId(base),
        ChannelId(f"{base}:sub"),
    ]
    member = next((c for c in Channels if c.value == base), None)
    if member is not None:
        forms.append(member)
    return forms


class TestChannels:
    def test_ms_teams_is_alias_of_msteams(self):
        # Channels.ms_teams is a deprecated back-compat alias of Channels.msteams.
        assert Channels.ms_teams is Channels.msteams
        assert Channels.ms_teams.value == "msteams"
        assert Channels.ms_teams.name == "msteams"
        # aliases are not included twice in iteration
        assert list(Channels).count(Channels.msteams) == 1

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_card_actions_accepts_all_formats(self, channel_id):
        # msteams supports up to 50 card actions regardless of how the channel is expressed.
        assert Channels.supports_card_actions(channel_id, 3) is True
        assert Channels.supports_card_actions(channel_id, 100) is False

    @pytest.mark.parametrize("channel_id", _forms("facebook"))
    def test_supports_card_actions_returns_false_over_limit(self, channel_id):
        assert Channels.supports_card_actions(channel_id, 3) is True
        assert Channels.supports_card_actions(channel_id, 4) is False

    def test_supports_card_actions_unknown_channel_is_false(self):
        assert Channels.supports_card_actions("some-unknown-channel", 1) is False

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_suggested_actions_accepts_all_formats(self, channel_id):
        assert Channels.supports_suggested_actions(channel_id, 3, "personal") is True
        assert Channels.supports_suggested_actions(channel_id, 3) is False

    @pytest.mark.parametrize("channel_id", _forms("webchat"))
    def test_supports_suggested_actions_returns_bool(self, channel_id):
        assert Channels.supports_suggested_actions(channel_id, 100) is True

    def test_supports_suggested_actions_unknown_channel_is_false(self):
        assert Channels.supports_suggested_actions("some-unknown-channel", 1) is False

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_has_message_feed_returns_true_for_msteams(self, channel_id):
        assert Channels.has_message_feed(channel_id) is True

    @pytest.mark.parametrize("channel_id", _forms("cortana"))
    def test_has_message_feed_returns_false_for_cortana(self, channel_id):
        assert Channels.has_message_feed(channel_id) is False

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_max_action_title_length_returns_int(self, channel_id):
        assert Channels.max_action_title_length(channel_id) == 20

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_video_card_returns_false_for_msteams(self, channel_id):
        assert Channels.supports_video_card(channel_id) is False

    @pytest.mark.parametrize("channel_id", _forms("webchat"))
    def test_supports_video_card_returns_true_for_webchat(self, channel_id):
        assert Channels.supports_video_card(channel_id) is True

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_create_conversation_returns_true_for_msteams(self, channel_id):
        assert Channels.supports_create_conversation(channel_id) is True

    @pytest.mark.parametrize("channel_id", _forms("alexa"))
    def test_supports_create_conversation_returns_false_for_alexa(self, channel_id):
        assert Channels.supports_create_conversation(channel_id) is False

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_update_activity_returns_true_for_msteams(self, channel_id):
        assert Channels.supports_update_activity(channel_id) is True

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_delete_activity_returns_true_for_msteams(self, channel_id):
        assert Channels.supports_delete_activity(channel_id) is True

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_receipt_card_returns_false_for_msteams(self, channel_id):
        assert Channels.supports_receipt_card(channel_id) is False

    @pytest.mark.parametrize("channel_id", _forms("webchat"))
    def test_supports_receipt_card_returns_true_for_webchat(self, channel_id):
        assert Channels.supports_receipt_card(channel_id) is True

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_thumbnail_card_returns_false_for_msteams(self, channel_id):
        assert Channels.supports_thumbnail_card(channel_id) is False

    @pytest.mark.parametrize("channel_id", _forms("webchat"))
    def test_supports_thumbnail_card_returns_true_for_webchat(self, channel_id):
        assert Channels.supports_thumbnail_card(channel_id) is True

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_audio_card_returns_false_for_msteams(self, channel_id):
        assert Channels.supports_audio_card(channel_id) is False

    @pytest.mark.parametrize("channel_id", _forms("webchat"))
    def test_supports_audio_card_returns_true_for_webchat(self, channel_id):
        assert Channels.supports_audio_card(channel_id) is True

    @pytest.mark.parametrize("channel_id", _forms("msteams") + [Channels.ms_teams])
    def test_supports_animation_card_returns_false_for_msteams(self, channel_id):
        assert Channels.supports_animation_card(channel_id) is False

    @pytest.mark.parametrize("channel_id", _forms("webchat"))
    def test_supports_animation_card_returns_true_for_webchat(self, channel_id):
        assert Channels.supports_animation_card(channel_id) is True
