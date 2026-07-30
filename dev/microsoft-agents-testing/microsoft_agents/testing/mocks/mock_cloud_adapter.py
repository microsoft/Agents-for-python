from microsoft_agents.hosting.core import (
    ChannelServiceAdapter,
    RestChannelServiceClientFactory,
)

def mock_cloud_adapter(adapter_cls: type[HttpAdapterBase]) -> Callable[]