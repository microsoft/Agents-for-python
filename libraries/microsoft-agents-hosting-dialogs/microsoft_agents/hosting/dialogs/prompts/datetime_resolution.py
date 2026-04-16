# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class DateTimeResolution:
    def __init__(
        self, value: str | None = None, start: str | None = None, end: str | None = None, timex: str | None = None
    ):
        self.value = value
        self.start = start
        self.end = end
        self.timex = timex