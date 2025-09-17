from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationReference,
)

from tests._common import TestingEnvironment, TEST_DEFAULTS
from tests._common.hosting_core._env import TestingUserTokenClientMixin, TestingActivityMixin

DEFAULTS = TEST_DEFAULTS()

class OAuthFlowTestEnv(TestingEnvironment, TestingUserTokenClientMixin, TestingActivityMixin):
    pass