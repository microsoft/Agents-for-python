# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class AgentTelemetryClient:
    """
    Interface for telemetry logging. Override to send telemetry to a custom sink.
    """

    def track_event(
        self,
        name: str,
        properties: dict[str, str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> None:
        pass

    def track_exception(
        self,
        exception: Exception,
        properties: dict[str, str] | None = None,
        measurements: dict[str, float] | None = None,
    ) -> None:
        pass

    def track_dependency(
        self,
        name: str,
        data: str | None = None,
        type_name: str | None = None,
        target: str | None = None,
        duration: int | None = None,
        success: bool = True,
        result_code: str | None = None,
        properties: dict[str, str] | None = None,
    ) -> None:
        pass

    def flush(self) -> None:
        pass


class NullTelemetryClient(AgentTelemetryClient):
    """
    No-op telemetry client. All calls are silently discarded.
    """

    def track_event(
        self,
        name: str,
        properties: dict[str, str] | None = None,
        metrics: dict[str, float] | None = None,
    ) -> None:
        pass

    def track_exception(
        self,
        exception: Exception,
        properties: dict[str, str] | None = None,
        measurements: dict[str, float] | None = None,
    ) -> None:
        pass

    def track_dependency(
        self,
        name: str,
        data: str | None = None,
        type_name: str | None = None,
        target: str | None = None,
        duration: int | None = None,
        success: bool = True,
        result_code: str | None = None,
        properties: dict[str, str] | None = None,
    ) -> None:
        pass

    def flush(self) -> None:
        pass
