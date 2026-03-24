from aiohttp.web import Request, Response

from microsoft_agents.hosting.core.telemetry import (
    attributes,
    SimpleSpanWrapper,
)


class _RequestSpanWrapper(SimpleSpanWrapper):

    def __init__(self, span_name: str):
        """Initializes the RequestSpanWrapper."""
        super().__init__(span_name)
        self._request: Request | None = None
        self._response: Response | None = None

    def _get_request_attributes(self) -> dict[str, str]:
        """Returns a dictionary of attributes related to the request to set on the span."""
        attr_dict = {}
        if self._request is not None:
            attr_dict[attributes.HTTP_METHOD] = self._request.method
        if self._response is not None:
            attr_dict[attributes.HTTP_STATUS_CODE] = self._response.status
        attr_dict[attributes.OPERATION] = self._span_name
        return attr_dict

    def share(
        self, request: Request | None = None, response: Response | None = None
    ) -> None:
        """Shares the span by setting the request and response attributes and ending the span. This should be called when the client operation is complete and a response is being sent back to the caller."""
        if request is not None:
            self._request = request
        if response is not None:
            self._response = response
