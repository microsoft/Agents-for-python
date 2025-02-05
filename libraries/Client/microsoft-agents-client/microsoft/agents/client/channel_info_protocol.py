from typing import Protocol


class ChannelInfoProtocol(Protocol):
    @property
    def id(self) -> str:
        raise NotImplementedError()

    @property.setter
    def id(self, value: str):
        raise NotImplementedError()

    @property
    def app_id(self) -> str:
        raise NotImplementedError()

    @property.setter
    def app_id(self, value: str):
        raise NotImplementedError()

    @property
    def resource_url(self) -> str:
        raise NotImplementedError()

    @property.setter
    def resource_url(self, value: str):
        raise NotImplementedError()

    @property
    def token_provider(self) -> str:
        raise NotImplementedError()

    @property.setter
    def token_provider(self, value: str):
        raise NotImplementedError()

    @property
    def channel_factory(self) -> str:
        raise NotImplementedError()

    @property.setter
    def channel_factory(self, value: str):
        raise NotImplementedError()

    @property
    def endpoint(self) -> str:
        raise NotImplementedError()

    @property.setter
    def endpoint(self, value: str):
        raise NotImplementedError()
