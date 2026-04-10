# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Dict, Optional


class BotTelemetryClient:
    """
    Interface for telemetry logging. Override to send telemetry to a custom sink.
    """

    def track_event(
        self,
        name: str,
        properties: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, float]] = None,
    ) -> None:
        pass

    def track_exception(
        self,
        exception: Exception,
        properties: Optional[Dict[str, str]] = None,
        measurements: Optional[Dict[str, float]] = None,
    ) -> None:
        pass

    def track_dependency(
        self,
        name: str,
        data: str = None,
        type_name: str = None,
        target: str = None,
        duration: int = None,
        success: bool = True,
        result_code: str = None,
        properties: Optional[Dict[str, str]] = None,
    ) -> None:
        pass

    def flush(self) -> None:
        pass


class NullTelemetryClient(BotTelemetryClient):
    """
    No-op telemetry client. All calls are silently discarded.
    """

    def track_event(
        self,
        name: str,
        properties: Optional[Dict[str, str]] = None,
        metrics: Optional[Dict[str, float]] = None,
    ) -> None:
        pass

    def track_exception(
        self,
        exception: Exception,
        properties: Optional[Dict[str, str]] = None,
        measurements: Optional[Dict[str, float]] = None,
    ) -> None:
        pass

    def track_dependency(
        self,
        name: str,
        data: str = None,
        type_name: str = None,
        target: str = None,
        duration: int = None,
        success: bool = True,
        result_code: str = None,
        properties: Optional[Dict[str, str]] = None,
    ) -> None:
        pass

    def flush(self) -> None:
        pass
