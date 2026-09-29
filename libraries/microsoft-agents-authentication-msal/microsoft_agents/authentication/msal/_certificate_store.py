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

DWORD = ctypes.c_uint32
BOOL = ctypes.c_int32
BYTE = ctypes.c_ubyte
HCERTSTORE = ctypes.c_void_p

X509_ASN_ENCODING = 0x00000001
PKCS_7_ASN_ENCODING = 0x00010000
CERT_ENCODING = X509_ASN_ENCODING | PKCS_7_ASN_ENCODING

CERT_FIND_SUBJECT_STR_W = 0x00080007


class _CERT_CONTEXT(ctypes.Structure):
    pass


PCCERT_CONTEXT = ctypes.POINTER(_CERT_CONTEXT)

_CERT_CONTEXT._fields_ = [
    ("dwCertEncodingType", DWORD),
    ("pbCertEncoded", ctypes.POINTER(BYTE)),
    ("cbCertEncoded", DWORD),
    ("pCertInfo", ctypes.c_void_p),
    ("hCertStore", HCERTSTORE),
]


def _configure_crypt32(crypt32) -> None:
    crypt32.CertOpenSystemStoreW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
    ]
    crypt32.CertOpenSystemStoreW.restype = HCERTSTORE

    crypt32.CertFindCertificateInStore.argtypes = [
        HCERTSTORE,
        DWORD,
        DWORD,
        DWORD,
        ctypes.c_wchar_p,
        PCCERT_CONTEXT,
    ]
    crypt32.CertFindCertificateInStore.restype = PCCERT_CONTEXT

    crypt32.CertDuplicateCertificateContext.argtypes = [PCCERT_CONTEXT]
    crypt32.CertDuplicateCertificateContext.restype = PCCERT_CONTEXT

    crypt32.CertFreeCertificateContext.argtypes = [PCCERT_CONTEXT]
    crypt32.CertFreeCertificateContext.restype = BOOL

    crypt32.CertCloseStore.argtypes = [HCERTSTORE, DWORD]
    crypt32.CertCloseStore.restype = BOOL


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

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    _configure_crypt32(crypt32)

    return crypt32


def _find_certificate_context(
    crypt32,
    *,
    subject_name: str,
    store_name: str,
) -> PCCERT_CONTEXT:
    """Find a certificate by subject name and return the certificate's duplicated context."""
    normalized_store_name = _normalize_store_name(store_name)

    store = crypt32.CertOpenSystemStoreW(None, normalized_store_name)
    if not store:
        raise OSError(f"Failed to open certificate store '{normalized_store_name}'.")

    certificate = None
    try:
        certificate = crypt32.CertFindCertificateInStore(
            store,
            CERT_ENCODING,
            0,
            CERT_FIND_SUBJECT_STR_W,
            subject_name,
            None,
        )
        if not certificate:
            raise LookupError(
                f"No certificate matching subject '{subject_name}' "
                f"was found in store '{normalized_store_name}'."
            )

        duplicate = crypt32.CertDuplicateCertificateContext(certificate)
        if not duplicate:
            raise OSError("Failed to duplicate certificate context.")

        return duplicate
    finally:
        if certificate:
            crypt32.CertFreeCertificateContext(certificate)

        crypt32.CertCloseStore(store, 0)
