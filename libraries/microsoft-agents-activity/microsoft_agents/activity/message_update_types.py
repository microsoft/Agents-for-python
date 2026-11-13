# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import StrEnum


class MessageUpdateTypes(StrEnum):
    EDIT_MESSAGE = "editMessage"
    SOFT_DELETE_MESSAGE = "softDeleteMessage"
    UNDELETE_MESSAGE = "undeleteMessage"
