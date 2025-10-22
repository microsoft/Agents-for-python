# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

class _Namespaces:
    """Storage key namespaces used by various components."""

    USER_AUTHORIZATION = "auth/{channel_id}/{user_id}"
    AUTHORIZATION = "auth/{channel_id}/{from_property_id}"