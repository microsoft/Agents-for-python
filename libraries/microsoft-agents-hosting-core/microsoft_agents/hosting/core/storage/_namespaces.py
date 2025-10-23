# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

class _Namespaces:
    """Storage key namespaces used by various components."""

    SIGN_IN_STATE = "auth.sign_in_state"
    USER_AUTHORIZATION = "auth.user_authorization.{channel_id}:{from_property_id}"