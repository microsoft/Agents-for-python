# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core.telemetry import (
    attributes,
    SimpleSpanWrapper,
)


class _RequestSpanWrapper(SimpleSpanWrapper):

    def __init__(self, span_name: str):
        """Initializes the RequestSpanWrapper."""
        super().__init__(span_name)
        self._http_method: str | None = None
        self._status_code: int | None = None

    def _get_request_attributes(self) -> dict[str, str]:
        """Returns a dictionary of attributes related to the request to set on the span."""
        attr_dict = {}
        if self._http_method is not None:
            attr_dict[attributes.HTTP_METHOD] = self._http_method
        if self._status_code is not None:
            attr_dict[attributes.HTTP_STATUS_CODE] = self._status_code
        attr_dict[attributes.OPERATION] = self._span_name
        return attr_dict

    def share(
        self, *, http_method: str | None = None, status_code: int | None = None
    ) -> None:
        """Shares the span by setting the request and response attributes and ending the span. This should be called when the client operation is complete and a response is being sent back to the caller."""
        self._http_method = http_method
        self._status_code = status_code
