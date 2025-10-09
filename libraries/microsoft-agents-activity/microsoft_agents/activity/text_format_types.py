# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum


class TextFormatTypes(str, Enum):
    markdown = "markdown"
    plain = "plain"
    xml = "xml"
