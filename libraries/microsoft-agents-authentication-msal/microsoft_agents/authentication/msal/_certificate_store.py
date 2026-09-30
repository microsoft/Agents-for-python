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
LONG = ctypes.c_int32
BOOL = ctypes.c_int32
BYTE = ctypes.c_ubyte
HCERTSTORE = ctypes.c_void_p
HCRYPTPROV_OR_NCRYPT_KEY_HANDLE = ctypes.c_size_t

X509_ASN_ENCODING = 0x00000001
PKCS_7_ASN_ENCODING = 0x00010000
CERT_ENCODING = X509_ASN_ENCODING | PKCS_7_ASN_ENCODING

CERT_FIND_SUBJECT_STR_W = 0x00080007
CERT_CHAIN_POLICY_BASE = 1
CRYPT_ACQUIRE_PREFER_NCRYPT_KEY_FLAG = 0x00020000

AT_SIGNATURE = 2
CERT_NCRYPT_KEY_SPEC = 0xFFFFFFFF


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


class _CERT_ENHKEY_USAGE(ctypes.Structure):
    _fields_ = [
        ("cUsageIdentifier", DWORD),
        ("rgpszUsageIdentifier", ctypes.POINTER(ctypes.c_char_p)),
    ]


class _CERT_USAGE_MATCH(ctypes.Structure):
    _fields_ = [
        ("dwType", DWORD),
        ("Usage", _CERT_ENHKEY_USAGE),
    ]


class _CERT_CHAIN_PARA(ctypes.Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("RequestedUsage", _CERT_USAGE_MATCH),
        ("RequestedIssuancePolicy", _CERT_USAGE_MATCH),
        ("dwUrlRetrievalTimeout", DWORD),
        ("fCheckRevocationFreshnessTime", BOOL),
        ("dwRevocationFreshnessTime", DWORD),
        ("pftCacheResync", ctypes.c_void_p),
        ("pStrongSignPara", ctypes.c_void_p),
        ("dwStrongSignFlags", DWORD),
    ]


class _CERT_CHAIN_POLICY_PARA(ctypes.Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("dwFlags", DWORD),
        ("pvExtraPolicyPara", ctypes.c_void_p),
    ]


class _CERT_CHAIN_POLICY_STATUS(ctypes.Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("dwError", DWORD),
        ("lChainIndex", LONG),
        ("lElementIndex", LONG),
        ("pvExtraPolicyStatus", ctypes.c_void_p),
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

    crypt32.CertGetCertificateChain.argtypes = [
        ctypes.c_void_p,
        PCCERT_CONTEXT,
        ctypes.c_void_p,
        HCERTSTORE,
        ctypes.POINTER(_CERT_CHAIN_PARA),
        DWORD,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    crypt32.CertGetCertificateChain.restype = BOOL

    crypt32.CertVerifyCertificateChainPolicy.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(_CERT_CHAIN_POLICY_PARA),
        ctypes.POINTER(_CERT_CHAIN_POLICY_STATUS),
    ]
    crypt32.CertVerifyCertificateChainPolicy.restype = BOOL

    crypt32.CertFreeCertificateChain.argtypes = [ctypes.c_void_p]
    crypt32.CertFreeCertificateChain.restype = None

    crypt32.CryptAcquireCertificatePrivateKey.argtypes = [
        PCCERT_CONTEXT,
        DWORD,
        ctypes.c_void_p,
        ctypes.POINTER(HCRYPTPROV_OR_NCRYPT_KEY_HANDLE),
        ctypes.POINTER(DWORD),
        ctypes.POINTER(BOOL),
    ]
    crypt32.CryptAcquireCertificatePrivateKey.restype = BOOL


def _configure_ncrypt(ncrypt) -> None:
    ncrypt.NCryptFreeObject.argtypes = [
        HCRYPTPROV_OR_NCRYPT_KEY_HANDLE,
    ]
    ncrypt.NCryptFreeObject.restype = LONG


def _configure_advapi32(advapi32) -> None:
    advapi32.CryptReleaseContext.argtypes = [
        HCRYPTPROV_OR_NCRYPT_KEY_HANDLE,
        DWORD,
    ]
    advapi32.CryptReleaseContext.restype = BOOL


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
    ncrypt = ctypes.WinDLL("ncrypt", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)

    _configure_crypt32(crypt32)
    _configure_ncrypt(ncrypt)
    _configure_advapi32(advapi32)

    return crypt32, ncrypt, advapi32


def _is_certificate_valid(crypt32, certificate: PCCERT_CONTEXT) -> bool:
    chain_parameters = _CERT_CHAIN_PARA()
    chain_parameters.cbSize = ctypes.sizeof(chain_parameters)

    chain_context = ctypes.c_void_p()

    if not crypt32.CertGetCertificateChain(
        None,
        certificate,
        None,
        None,
        ctypes.byref(chain_parameters),
        0,
        None,
        ctypes.byref(chain_context),
    ):
        raise OSError("Failed to build certificate chain.")

    try:
        policy_parameters = _CERT_CHAIN_POLICY_PARA()
        policy_parameters.cbSize = ctypes.sizeof(policy_parameters)

        policy_status = _CERT_CHAIN_POLICY_STATUS()
        policy_status.cbSize = ctypes.sizeof(policy_status)

        if not crypt32.CertVerifyCertificateChainPolicy(
            ctypes.c_void_p(CERT_CHAIN_POLICY_BASE),
            chain_context,
            ctypes.byref(policy_parameters),
            ctypes.byref(policy_status),
        ):
            raise OSError("Failed to verify certificate chain policy.")

        return policy_status.dwError == 0
    finally:
        crypt32.CertFreeCertificateChain(chain_context)


def _find_certificate_context(
    crypt32,
    *,
    subject_name: str,
    store_name: str,
    valid_only: bool,
) -> PCCERT_CONTEXT:
    """Find a matching certificate and return the certificate's duplicated context."""
    normalized_store_name = _normalize_store_name(store_name)

    store = crypt32.CertOpenSystemStoreW(None, normalized_store_name)
    if not store:
        raise OSError(f"Failed to open certificate store '{normalized_store_name}'.")

    certificate = None
    try:
        while True:
            certificate = crypt32.CertFindCertificateInStore(
                store,
                CERT_ENCODING,
                0,
                CERT_FIND_SUBJECT_STR_W,
                subject_name,
                certificate,
            )

            if not certificate:
                raise LookupError(
                    f"No certificate matching subject '{subject_name}' "
                    f"was found in store '{normalized_store_name}'."
                )

            if valid_only and not _is_certificate_valid(crypt32, certificate):
                continue

            duplicate = crypt32.CertDuplicateCertificateContext(certificate)
            if not duplicate:
                raise OSError("Failed to duplicate certificate context.")

            return duplicate
    finally:
        if certificate:
            crypt32.CertFreeCertificateContext(certificate)

        crypt32.CertCloseStore(store, 0)


def _acquire_private_key(
    crypt32,
    certificate: PCCERT_CONTEXT,
) -> tuple[int, int, bool]:
    key_handle = HCRYPTPROV_OR_NCRYPT_KEY_HANDLE()
    key_spec = DWORD()
    caller_free = BOOL()

    if not crypt32.CryptAcquireCertificatePrivateKey(
        certificate,
        CRYPT_ACQUIRE_PREFER_NCRYPT_KEY_FLAG,
        None,
        ctypes.byref(key_handle),
        ctypes.byref(key_spec),
        ctypes.byref(caller_free),
    ):
        raise OSError("Failed to acquire certificate private key.")

    return key_handle.value, key_spec.value, bool(caller_free.value)


def _release_private_key(
    ncrypt,
    advapi32,
    *,
    key_handle: int,
    key_spec: int,
    caller_free: bool,
) -> None:
    if not caller_free:
        return

    if key_spec == CERT_NCRYPT_KEY_SPEC:
        if ncrypt.NCryptFreeObject(key_handle) != 0:
            raise OSError("Failed to release CNG private key.")
        return

    if not advapi32.CryptReleaseContext(key_handle, 0):
        raise OSError("Failed to release certificate private key provider.")
