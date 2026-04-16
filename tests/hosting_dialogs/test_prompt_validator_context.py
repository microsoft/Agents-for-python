# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.hosting.dialogs import DialogSet
from microsoft_agents.hosting.core import MemoryStorage, ConversationState


class TestPromptValidatorContext:

    @pytest.mark.asyncio
    async def test_prompt_validator_context_end(self):
        storage = MemoryStorage()
        conv = ConversationState(storage)
        accessor = conv.create_property("dialogstate")
        dialog_set = DialogSet(accessor)
        assert dialog_set is not None

    def test_prompt_validator_context_retry_end(self):
        storage = MemoryStorage()
        conv = ConversationState(storage)
        accessor = conv.create_property("dialogstate")
        dialog_set = DialogSet(accessor)
        assert dialog_set is not None
