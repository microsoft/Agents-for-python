# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import List

import pytest

from microsoft_agents.hosting.dialogs.choices import (
    Choice,
    ChoiceFactory,
    ChoiceFactoryOptions,
)
from microsoft_agents.activity import (
    ActionTypes,
    Activity,
    ActivityTypes,
    Attachment,
    AttachmentLayoutTypes,
    CardAction,
    HeroCard,
    InputHints,
    SuggestedActions,
    Channels,
)


class TestChoiceFactory:
    color_choices: List[Choice] = [Choice("red"), Choice("green"), Choice("blue")]
    choices_with_actions: List[Choice] = [
        Choice(
            "ImBack",
            action=CardAction(
                type=ActionTypes.im_back, title="ImBack Action", value="ImBack Value"
            ),
        ),
        Choice(
            "MessageBack",
            action=CardAction(
                type=ActionTypes.message_back,
                title="MessageBack Action",
                value="MessageBack Value",
            ),
        ),
        Choice(
            "PostBack",
            action=CardAction(
                type=ActionTypes.post_back,
                title="PostBack Action",
                value="PostBack Value",
            ),
        ),
    ]

    def test_inline_should_render_choices_inline(self):
        activity = ChoiceFactory.inline(TestChoiceFactory.color_choices, "select from:")
        assert "select from: (1) red, (2) green, or (3) blue" == activity.text

    def test_should_render_choices_as_a_list(self):
        activity = ChoiceFactory.list_style(
            TestChoiceFactory.color_choices, "select from:"
        )
        assert "select from:\n\n   1. red\n   2. green\n   3. blue" == activity.text

    def test_should_render_unincluded_numbers_choices_as_a_list(self):
        activity = ChoiceFactory.list_style(
            TestChoiceFactory.color_choices,
            "select from:",
            options=ChoiceFactoryOptions(include_numbers=False),
        )
        assert "select from:\n\n   - red\n   - green\n   - blue" == activity.text

    def test_should_render_choices_as_suggested_actions(self):
        expected = Activity(
            type=ActivityTypes.message,
            text="select from:",
            input_hint=InputHints.expecting_input,
            suggested_actions=SuggestedActions(
                actions=[
                    CardAction(type=ActionTypes.im_back, value="red", title="red"),
                    CardAction(type=ActionTypes.im_back, value="green", title="green"),
                    CardAction(type=ActionTypes.im_back, value="blue", title="blue"),
                ]
            ),
        )

        activity = ChoiceFactory.suggested_action(
            TestChoiceFactory.color_choices, "select from:"
        )

        assert expected == activity

    def test_should_render_choices_as_hero_card(self):
        expected = Activity(
            type=ActivityTypes.message,
            input_hint=InputHints.expecting_input,
            attachment_layout=AttachmentLayoutTypes.list,
            attachments=[
                Attachment(
                    content=HeroCard(
                        text="select from:",
                        buttons=[
                            CardAction(
                                type=ActionTypes.im_back, value="red", title="red"
                            ),
                            CardAction(
                                type=ActionTypes.im_back, value="green", title="green"
                            ),
                            CardAction(
                                type=ActionTypes.im_back, value="blue", title="blue"
                            ),
                        ],
                    ),
                    content_type="application/vnd.microsoft.card.hero",
                )
            ],
        )

        activity = ChoiceFactory.hero_card(
            TestChoiceFactory.color_choices, "select from:"
        )

        assert expected == activity

    def test_should_automatically_choose_render_style_based_on_channel_type(self):
        expected = Activity(
            type=ActivityTypes.message,
            text="select from:",
            input_hint=InputHints.expecting_input,
            suggested_actions=SuggestedActions(
                actions=[
                    CardAction(type=ActionTypes.im_back, value="red", title="red"),
                    CardAction(type=ActionTypes.im_back, value="green", title="green"),
                    CardAction(type=ActionTypes.im_back, value="blue", title="blue"),
                ]
            ),
        )
        activity = ChoiceFactory.for_channel(
            Channels.emulator, TestChoiceFactory.color_choices, "select from:"
        )

        assert expected == activity

    def test_should_choose_correct_styles_for_teams(self):
        expected = Activity(
            type=ActivityTypes.message,
            input_hint=InputHints.expecting_input,
            attachment_layout=AttachmentLayoutTypes.list,
            attachments=[
                Attachment(
                    content=HeroCard(
                        text="select from:",
                        buttons=[
                            CardAction(
                                type=ActionTypes.im_back, value="red", title="red"
                            ),
                            CardAction(
                                type=ActionTypes.im_back, value="green", title="green"
                            ),
                            CardAction(
                                type=ActionTypes.im_back, value="blue", title="blue"
                            ),
                        ],
                    ),
                    content_type="application/vnd.microsoft.card.hero",
                )
            ],
        )
        activity = ChoiceFactory.for_channel(
            Channels.ms_teams, TestChoiceFactory.color_choices, "select from:"
        )
        assert expected == activity

    def test_should_include_choice_actions_in_suggested_actions(self):
        expected = Activity(
            type=ActivityTypes.message,
            text="select from:",
            input_hint=InputHints.expecting_input,
            suggested_actions=SuggestedActions(
                actions=[
                    CardAction(
                        type=ActionTypes.im_back,
                        value="ImBack Value",
                        title="ImBack Action",
                    ),
                    CardAction(
                        type=ActionTypes.message_back,
                        value="MessageBack Value",
                        title="MessageBack Action",
                    ),
                    CardAction(
                        type=ActionTypes.post_back,
                        value="PostBack Value",
                        title="PostBack Action",
                    ),
                ]
            ),
        )
        activity = ChoiceFactory.suggested_action(
            TestChoiceFactory.choices_with_actions, "select from:"
        )
        assert expected == activity

    def test_should_include_choice_actions_in_hero_cards(self):
        expected = Activity(
            type=ActivityTypes.message,
            input_hint=InputHints.expecting_input,
            attachment_layout=AttachmentLayoutTypes.list,
            attachments=[
                Attachment(
                    content=HeroCard(
                        text="select from:",
                        buttons=[
                            CardAction(
                                type=ActionTypes.im_back,
                                value="ImBack Value",
                                title="ImBack Action",
                            ),
                            CardAction(
                                type=ActionTypes.message_back,
                                value="MessageBack Value",
                                title="MessageBack Action",
                            ),
                            CardAction(
                                type=ActionTypes.post_back,
                                value="PostBack Value",
                                title="PostBack Action",
                            ),
                        ],
                    ),
                    content_type="application/vnd.microsoft.card.hero",
                )
            ],
        )
        activity = ChoiceFactory.hero_card(
            TestChoiceFactory.choices_with_actions, "select from:"
        )
        assert expected == activity
