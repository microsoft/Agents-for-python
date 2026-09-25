# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

import ctypes
import sys

_STORE_NAMES = {
    "addressbook": "AddressBook",
    "authroot": "AuthRoot",
    "certificateauthority": "CA",
    "disallowed": "Disallowed",
    "my": "My",
    "root": "Root",
    "trustedpeople": "TrustedPeople",
    "trustedpublisher": "TrustedPublisher",
}


def _normalize_store_name(store_name: str | None) -> str:
    if not store_name:
        return "My"

    return _STORE_NAMES.get(store_name.casefold(), "My")


def _load_windows_apis():
    if sys.platform != "win32":
        raise OSError(
            "CertificateSubjectName authentication requires "
            "the Windows certificate store."
        )

    return ctypes.WinDLL("crypt32", use_last_error=True)
