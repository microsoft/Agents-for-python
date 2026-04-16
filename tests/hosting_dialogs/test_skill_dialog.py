# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# SkillDialog tests require BotFrameworkSkill, BotFrameworkClient, and
# ConversationIdFactoryBase infrastructure from botbuilder that is not
# available in the new Microsoft Agents SDK. All tests are skipped.

import pytest


@pytest.mark.skip(
    reason="Requires BotFrameworkSkill/BotFrameworkClient skill infrastructure not available in new SDK"
)
class TestSkillDialog:
    async def test_constructor_validation_test(self):
        pass

    async def test_begin_dialog_options_validation(self):
        pass

    async def test_begin_dialog_calls_skill_no_deliverymode(self):
        pass

    async def test_begin_dialog_calls_skill_expect_replies(self):
        pass

    async def test_should_handle_invoke_activities(self):
        pass

    async def test_cancel_dialog_sends_eoc(self):
        pass

    async def test_should_throw_on_post_failure(self):
        pass

    async def test_should_intercept_oauth_cards_for_sso(self):
        pass

    async def test_should_not_intercept_oauth_cards_for_empty_connection_name(self):
        pass

    async def test_should_not_intercept_oauth_cards_for_empty_token(self):
        pass

    async def test_should_not_intercept_oauth_cards_for_token_exception(self):
        pass

    async def test_should_not_intercept_oauth_cards_for_bad_request(self):
        pass

    async def test_end_of_conversation_from_expect_replies_calls_delete_conversation_reference(
        self,
    ):
        pass
