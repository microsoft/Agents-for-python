# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.testing import TestAdapter, TestFlow

@pytest.fixture
def flow() -> TestFlow:
    from app import AGENT_APP

    adapter = TestAdapter()
    return TestFlow(adapter, AGENT_APP.on_turn)
