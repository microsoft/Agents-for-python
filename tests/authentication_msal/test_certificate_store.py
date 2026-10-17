import base64
import ctypes
import hashlib
import json
import uuid

import pytest
from microsoft_agents.authentication.msal._certificate_store import (
    _CERT_CONTEXT,
    AT_KEYEXCHANGE,
    AT_SIGNATURE,
    CALG_RSA_KEYX,
    CALG_RSA_SIGN,
    CERT_ENCODING,
    CERT_FIND_SUBJECT_STR_W,
    CERT_NCRYPT_KEY_SPEC,
    _acquire_private_key,
    _CertificateStoreClientAssertion,
    _compute_certificate_thumbprint,
    _find_certificate_context,
    _get_certificate_raw_data,
    _is_certificate_valid,
    _is_cng_key_rsa,
    _is_legacy_key_rsa,
    _is_private_key_rsa,
    _load_windows_apis,
    _normalize_store_name,
    _release_private_key,
    _sign_hash_with_cng,
    _sign_hash_with_cng_pkcs1,
    _sign_hash_with_legacy_csp,
)


def test_load_windows_apis_raises_on_non_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")

    with pytest.raises(
        OSError,
        match="CertificateSubjectName authentication requires the Windows certificate store",
    ):
        _load_windows_apis()


@pytest.mark.parametrize(
    ("store_name", "expected"),
    [
        (None, "My"),
        ("", "My"),
        ("My", "My"),
        ("my", "My"),
        ("Root", "Root"),
        ("ROOT", "Root"),
        ("CertificateAuthority", "CA"),
        ("certificateauthority", "CA"),
        ("TrustedPeople", "TrustedPeople"),
        ("invalid-store", "invalid-store"),
        ("AddressBook", "AddressBook"),
        ("authroot", "AuthRoot"),
        ("Disallowed", "Disallowed"),
        ("trustedpublisher", "TrustedPublisher"),
    ],
)
def test_normalize_store_name(store_name, expected):
    assert _normalize_store_name(store_name) == expected


def test_find_certificate_context_duplicates_certificate(mocker):
    crypt32 = mocker.Mock()

    store = ctypes.c_void_p(1)
    certificate = ctypes.pointer(_CERT_CONTEXT())
    duplicate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CertOpenSystemStoreW.return_value = store
    crypt32.CertFindCertificateInStore.return_value = certificate
    crypt32.CertDuplicateCertificateContext.return_value = duplicate

    result = _find_certificate_context(
        crypt32,
        subject_name="test-agent",
        store_name="my",
        valid_only=False,
    )

    assert result is duplicate
    crypt32.CertOpenSystemStoreW.assert_called_once_with(None, "My")
    crypt32.CertFindCertificateInStore.assert_called_once_with(
        store,
        CERT_ENCODING,
        0,
        CERT_FIND_SUBJECT_STR_W,
        "test-agent",
        None,
    )
    crypt32.CertDuplicateCertificateContext.assert_called_once_with(certificate)
    crypt32.CertGetCertificateChain.assert_not_called()
    crypt32.CertFreeCertificateContext.assert_called_once_with(certificate)
    crypt32.CertCloseStore.assert_called_once_with(store, 0)


def test_find_certificate_context_closes_store_when_not_found(mocker):
    crypt32 = mocker.Mock()
    store = ctypes.c_void_p(1)

    crypt32.CertOpenSystemStoreW.return_value = store
    crypt32.CertFindCertificateInStore.return_value = None

    with pytest.raises(LookupError, match="test-agent"):
        _find_certificate_context(
            crypt32,
            subject_name="test-agent",
            store_name="My",
            valid_only=False,
        )

    crypt32.CertFreeCertificateContext.assert_not_called()
    crypt32.CertCloseStore.assert_called_once_with(store, 0)


def test_find_certificate_context_raises_when_store_cannot_be_opened(mocker):
    crypt32 = mocker.Mock()
    crypt32.CertOpenSystemStoreW.return_value = None

    with pytest.raises(OSError, match="Failed to open certificate store 'My'"):
        _find_certificate_context(
            crypt32,
            subject_name="test-agent",
            store_name="My",
            valid_only=False,
        )

    crypt32.CertFindCertificateInStore.assert_not_called()
    crypt32.CertCloseStore.assert_not_called()


def test_find_certificate_context_frees_resources_when_duplication_fails(mocker):
    crypt32 = mocker.Mock()

    store = ctypes.c_void_p(1)
    certificate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CertOpenSystemStoreW.return_value = store
    crypt32.CertFindCertificateInStore.return_value = certificate
    crypt32.CertDuplicateCertificateContext.return_value = None

    with pytest.raises(OSError, match="Failed to duplicate certificate context"):
        _find_certificate_context(
            crypt32,
            subject_name="test-agent",
            store_name="My",
            valid_only=False,
        )

    crypt32.CertFreeCertificateContext.assert_called_once_with(certificate)
    crypt32.CertCloseStore.assert_called_once_with(store, 0)


def test_is_certificate_valid_when_chain_policy_succeeds(mocker):
    crypt32 = mocker.Mock()
    certificate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CertGetCertificateChain.return_value = True
    crypt32.CertVerifyCertificateChainPolicy.return_value = True

    assert _is_certificate_valid(crypt32, certificate)

    crypt32.CertFreeCertificateChain.assert_called_once()


def test_is_certificate_valid_when_chain_policy_rejects_certificate(mocker):
    crypt32 = mocker.Mock()
    certificate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CertGetCertificateChain.return_value = True

    def set_policy_error(_, __, ___, policy_status):
        policy_status._obj.dwError = 1
        return True

    crypt32.CertVerifyCertificateChainPolicy.side_effect = set_policy_error

    assert not _is_certificate_valid(crypt32, certificate)

    crypt32.CertFreeCertificateChain.assert_called_once()


def test_is_certificate_valid_raises_when_chain_cannot_be_built(mocker):
    crypt32 = mocker.Mock()
    certificate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CertGetCertificateChain.return_value = False

    with pytest.raises(OSError, match="Failed to build certificate chain"):
        _is_certificate_valid(crypt32, certificate)

    crypt32.CertVerifyCertificateChainPolicy.assert_not_called()
    crypt32.CertFreeCertificateChain.assert_not_called()


def test_is_certificate_valid_raises_when_chain_policy_cannot_be_verified(mocker):
    crypt32 = mocker.Mock()
    certificate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CertGetCertificateChain.return_value = True
    crypt32.CertVerifyCertificateChainPolicy.return_value = False

    with pytest.raises(OSError, match="Failed to verify certificate chain policy"):
        _is_certificate_valid(crypt32, certificate)

    crypt32.CertFreeCertificateChain.assert_called_once()


def test_find_certificate_context_validates_certificate_when_required(mocker):
    crypt32 = mocker.Mock()

    store = ctypes.c_void_p(1)
    certificate = ctypes.pointer(_CERT_CONTEXT())
    duplicate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CertOpenSystemStoreW.return_value = store
    crypt32.CertFindCertificateInStore.return_value = certificate
    crypt32.CertDuplicateCertificateContext.return_value = duplicate
    crypt32.CertGetCertificateChain.return_value = True
    crypt32.CertVerifyCertificateChainPolicy.return_value = True

    result = _find_certificate_context(
        crypt32,
        subject_name="test-agent",
        store_name="My",
        valid_only=True,
    )

    assert result is duplicate
    crypt32.CertGetCertificateChain.assert_called_once()


def test_find_certificate_context_skips_invalid_certificate(mocker):
    crypt32 = mocker.Mock()

    store = ctypes.c_void_p(1)
    invalid_certificate = ctypes.pointer(_CERT_CONTEXT())
    valid_certificate = ctypes.pointer(_CERT_CONTEXT())
    duplicate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CertOpenSystemStoreW.return_value = store
    crypt32.CertFindCertificateInStore.side_effect = [
        invalid_certificate,
        valid_certificate,
    ]
    crypt32.CertDuplicateCertificateContext.return_value = duplicate

    crypt32.CertGetCertificateChain.return_value = True

    policy_errors = iter([1, 0])

    def set_policy_error(_, __, ___, policy_status):
        policy_status._obj.dwError = next(policy_errors)
        return True

    crypt32.CertVerifyCertificateChainPolicy.side_effect = set_policy_error

    result = _find_certificate_context(
        crypt32,
        subject_name="test-agent",
        store_name="My",
        valid_only=True,
    )

    assert result is duplicate

    assert crypt32.CertFindCertificateInStore.call_count == 2

    first_call = crypt32.CertFindCertificateInStore.call_args_list[0]
    second_call = crypt32.CertFindCertificateInStore.call_args_list[1]

    assert first_call.args[-1] is None
    assert second_call.args[-1] is invalid_certificate

    crypt32.CertDuplicateCertificateContext.assert_called_once_with(valid_certificate)
    crypt32.CertFreeCertificateContext.assert_called_once_with(valid_certificate)
    crypt32.CertCloseStore.assert_called_once_with(store, 0)


def test_find_certificate_context_raises_when_all_certificates_are_invalid(mocker):
    crypt32 = mocker.Mock()

    store = ctypes.c_void_p(1)
    invalid_certificate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CertOpenSystemStoreW.return_value = store
    crypt32.CertFindCertificateInStore.side_effect = [
        invalid_certificate,
        None,
    ]
    crypt32.CertGetCertificateChain.return_value = True

    def set_policy_error(_, __, ___, policy_status):
        policy_status._obj.dwError = 1
        return True

    crypt32.CertVerifyCertificateChainPolicy.side_effect = set_policy_error

    with pytest.raises(LookupError, match="test-agent"):
        _find_certificate_context(
            crypt32,
            subject_name="test-agent",
            store_name="My",
            valid_only=True,
        )

    assert crypt32.CertFindCertificateInStore.call_count == 2

    first_call = crypt32.CertFindCertificateInStore.call_args_list[0]
    second_call = crypt32.CertFindCertificateInStore.call_args_list[1]

    assert first_call.args[-1] is None
    assert second_call.args[-1] is invalid_certificate

    crypt32.CertDuplicateCertificateContext.assert_not_called()
    crypt32.CertFreeCertificateContext.assert_not_called()
    crypt32.CertCloseStore.assert_called_once_with(store, 0)


def test_acquire_private_key_returns_cng_key(mocker):
    crypt32 = mocker.Mock()
    certificate = ctypes.pointer(_CERT_CONTEXT())

    def acquire_key(_, __, ___, key_handle, key_spec, caller_free):
        key_handle._obj.value = 123
        key_spec._obj.value = 0xFFFFFFFF
        caller_free._obj.value = True
        return True

    crypt32.CryptAcquireCertificatePrivateKey.side_effect = acquire_key

    result = _acquire_private_key(crypt32, certificate)

    assert result == (123, 0xFFFFFFFF, True)


def test_acquire_private_key_returns_legacy_key(mocker):
    crypt32 = mocker.Mock()
    certificate = ctypes.pointer(_CERT_CONTEXT())

    def acquire_key(_, __, ___, key_handle, key_spec, caller_free):
        key_handle._obj.value = 456
        key_spec._obj.value = 2
        caller_free._obj.value = False
        return True

    crypt32.CryptAcquireCertificatePrivateKey.side_effect = acquire_key

    result = _acquire_private_key(crypt32, certificate)

    assert result == (456, 2, False)


def test_acquire_private_key_raises_when_acquisition_fails(mocker):
    crypt32 = mocker.Mock()
    certificate = ctypes.pointer(_CERT_CONTEXT())

    crypt32.CryptAcquireCertificatePrivateKey.return_value = False

    with pytest.raises(OSError, match="Failed to acquire certificate private key"):
        _acquire_private_key(crypt32, certificate)


def test_release_private_key_releases_cng_key(mocker):
    ncrypt = mocker.Mock()
    advapi32 = mocker.Mock()

    ncrypt.NCryptFreeObject.return_value = 0

    _release_private_key(
        ncrypt,
        advapi32,
        key_handle=123,
        key_spec=CERT_NCRYPT_KEY_SPEC,
        caller_free=True,
    )

    ncrypt.NCryptFreeObject.assert_called_once_with(123)
    advapi32.CryptReleaseContext.assert_not_called()


def test_release_private_key_releases_legacy_provider(mocker):
    ncrypt = mocker.Mock()
    advapi32 = mocker.Mock()

    advapi32.CryptReleaseContext.return_value = True

    _release_private_key(
        ncrypt,
        advapi32,
        key_handle=456,
        key_spec=AT_SIGNATURE,
        caller_free=True,
    )

    advapi32.CryptReleaseContext.assert_called_once_with(456, 0)
    ncrypt.NCryptFreeObject.assert_not_called()


def test_release_private_key_does_not_release_unowned_handle(mocker):
    ncrypt = mocker.Mock()
    advapi32 = mocker.Mock()

    _release_private_key(
        ncrypt,
        advapi32,
        key_handle=123,
        key_spec=CERT_NCRYPT_KEY_SPEC,
        caller_free=False,
    )

    ncrypt.NCryptFreeObject.assert_not_called()
    advapi32.CryptReleaseContext.assert_not_called()


def test_release_private_key_raises_when_cng_release_fails(mocker):
    ncrypt = mocker.Mock()
    advapi32 = mocker.Mock()

    ncrypt.NCryptFreeObject.return_value = 1

    with pytest.raises(OSError, match="Failed to release CNG private key"):
        _release_private_key(
            ncrypt,
            advapi32,
            key_handle=123,
            key_spec=CERT_NCRYPT_KEY_SPEC,
            caller_free=True,
        )

    advapi32.CryptReleaseContext.assert_not_called()


def test_release_private_key_raises_when_legacy_release_fails(mocker):
    ncrypt = mocker.Mock()
    advapi32 = mocker.Mock()

    advapi32.CryptReleaseContext.return_value = False

    with pytest.raises(
        OSError,
        match="Failed to release certificate private key provider",
    ):
        _release_private_key(
            ncrypt,
            advapi32,
            key_handle=456,
            key_spec=AT_SIGNATURE,
            caller_free=True,
        )

    ncrypt.NCryptFreeObject.assert_not_called()


def test_is_cng_key_rsa_returns_true_for_rsa(mocker):
    ncrypt = mocker.Mock()
    encoded_algorithm = "RSA\0".encode("utf-16-le")

    def get_property(_, __, buffer, ___, result_size, ____):
        result_size._obj.value = len(encoded_algorithm)

        if buffer is not None:
            for index, value in enumerate(encoded_algorithm):
                buffer[index] = value

        return 0

    ncrypt.NCryptGetProperty.side_effect = get_property

    assert _is_cng_key_rsa(ncrypt, 123)


def test_is_cng_key_rsa_returns_false_for_non_rsa(mocker):
    ncrypt = mocker.Mock()
    encoded_algorithm = "ECDSA\0".encode("utf-16-le")

    def get_property(_, __, buffer, ___, result_size, ____):
        result_size._obj.value = len(encoded_algorithm)

        if buffer is not None:
            for index, value in enumerate(encoded_algorithm):
                buffer[index] = value

        return 0

    ncrypt.NCryptGetProperty.side_effect = get_property

    assert not _is_cng_key_rsa(ncrypt, 123)


@pytest.mark.parametrize("algorithm", [CALG_RSA_SIGN, CALG_RSA_KEYX])
def test_is_legacy_key_rsa_returns_true_for_rsa(mocker, algorithm):
    advapi32 = mocker.Mock()

    def get_user_key(_, __, user_key):
        user_key._obj.value = 789
        return True

    def get_key_param(_, __, algorithm_buffer, ___, ____):
        ctypes.cast(
            algorithm_buffer,
            ctypes.POINTER(ctypes.c_uint32),
        ).contents.value = algorithm
        return True

    advapi32.CryptGetUserKey.side_effect = get_user_key
    advapi32.CryptGetKeyParam.side_effect = get_key_param
    advapi32.CryptDestroyKey.return_value = True

    assert _is_legacy_key_rsa(
        advapi32,
        key_handle=456,
        key_spec=AT_SIGNATURE,
    )

    advapi32.CryptDestroyKey.assert_called_once_with(789)


def test_is_legacy_key_rsa_returns_false_for_non_rsa(mocker):
    advapi32 = mocker.Mock()

    def get_user_key(_, __, user_key):
        user_key._obj.value = 789
        return True

    def get_key_param(_, __, algorithm_buffer, ___, ____):
        ctypes.cast(
            algorithm_buffer,
            ctypes.POINTER(ctypes.c_uint32),
        ).contents.value = 0
        return True

    advapi32.CryptGetUserKey.side_effect = get_user_key
    advapi32.CryptGetKeyParam.side_effect = get_key_param
    advapi32.CryptDestroyKey.return_value = True

    assert not _is_legacy_key_rsa(
        advapi32,
        key_handle=456,
        key_spec=AT_KEYEXCHANGE,
    )


def test_is_private_key_rsa_uses_cng_for_ncrypt_key(mocker):
    ncrypt = mocker.Mock()
    advapi32 = mocker.Mock()

    encoded_algorithm = "RSA\0".encode("utf-16-le")

    def get_property(_, __, buffer, ___, result_size, ____):
        result_size._obj.value = len(encoded_algorithm)
        if buffer is not None:
            for index, value in enumerate(encoded_algorithm):
                buffer[index] = value
        return 0

    ncrypt.NCryptGetProperty.side_effect = get_property

    assert _is_private_key_rsa(
        ncrypt,
        advapi32,
        key_handle=123,
        key_spec=CERT_NCRYPT_KEY_SPEC,
    )

    advapi32.CryptGetUserKey.assert_not_called()


def test_sign_hash_with_cng_returns_signature(mocker):
    ncrypt = mocker.Mock()
    digest = bytes(range(32))
    expected_signature = b"\x01\x02\x03\x04"

    def sign_hash(
        _key_handle,
        _padding_info,
        _digest,
        _digest_size,
        signature,
        _signature_buffer_size,
        result_size,
        _flags,
    ):
        result_size._obj.value = len(expected_signature)

        if signature is not None:
            for index, value in enumerate(expected_signature):
                signature[index] = value

        return 0

    ncrypt.NCryptSignHash.side_effect = sign_hash

    result = _sign_hash_with_cng(
        ncrypt,
        key_handle=123,
        digest=digest,
    )

    assert result == expected_signature
    assert ncrypt.NCryptSignHash.call_count == 2


def test_sign_hash_with_cng_requires_sha256_digest(mocker):
    ncrypt = mocker.Mock()

    with pytest.raises(ValueError, match="SHA-256 digest"):
        _sign_hash_with_cng(
            ncrypt,
            key_handle=123,
            digest=b"invalid",
        )

    ncrypt.NCryptSignHash.assert_not_called()


def test_sign_hash_with_cng_raises_when_signing_fails(mocker):
    ncrypt = mocker.Mock()
    digest = bytes(32)

    def sign_hash(
        _key_handle,
        _padding_info,
        _digest,
        _digest_size,
        signature,
        _signature_buffer_size,
        result_size,
        _flags,
    ):
        if signature is None:
            result_size._obj.value = 256
            return 0

        return 1

    ncrypt.NCryptSignHash.side_effect = sign_hash

    with pytest.raises(OSError, match="Failed to sign with CNG private key"):
        _sign_hash_with_cng(
            ncrypt,
            key_handle=123,
            digest=digest,
        )


def test_sign_hash_with_legacy_csp_returns_signature(mocker):
    advapi32 = mocker.Mock()
    digest = bytes(range(32))

    native_signature = b"\x01\x02\x03\x04"

    def create_hash(
        _provider_handle,
        _algorithm,
        _key,
        _flags,
        hash_handle,
    ):
        hash_handle._obj.value = 789
        return True

    def sign_hash(
        _hash_handle,
        _key_spec,
        _description,
        _flags,
        signature,
        signature_size,
    ):
        signature_size._obj.value = len(native_signature)

        if signature is not None:
            for index, value in enumerate(native_signature):
                signature[index] = value

        return True

    advapi32.CryptCreateHash.side_effect = create_hash
    advapi32.CryptSetHashParam.return_value = True
    advapi32.CryptSignHashW.side_effect = sign_hash
    advapi32.CryptDestroyHash.return_value = True

    result = _sign_hash_with_legacy_csp(
        advapi32,
        key_handle=456,
        key_spec=AT_SIGNATURE,
        digest=digest,
    )

    assert result == native_signature[::-1]
    assert advapi32.CryptSignHashW.call_count == 2
    advapi32.CryptDestroyHash.assert_called_once_with(789)


def test_sign_hash_with_legacy_csp_requires_sha256_digest(mocker):
    advapi32 = mocker.Mock()

    with pytest.raises(ValueError, match="SHA-256 digest"):
        _sign_hash_with_legacy_csp(
            advapi32,
            key_handle=456,
            key_spec=AT_SIGNATURE,
            digest=b"invalid",
        )

    advapi32.CryptCreateHash.assert_not_called()


def test_sign_hash_with_legacy_csp_raises_when_signing_fails(mocker):
    advapi32 = mocker.Mock()
    digest = bytes(32)

    def create_hash(
        _provider_handle,
        _algorithm,
        _key,
        _flags,
        hash_handle,
    ):
        hash_handle._obj.value = 789
        return True

    def sign_hash(
        _hash_handle,
        _key_spec,
        _description,
        _flags,
        signature,
        signature_size,
    ):
        if signature is None:
            signature_size._obj.value = 256
            return True

        return False

    advapi32.CryptCreateHash.side_effect = create_hash
    advapi32.CryptSetHashParam.return_value = True
    advapi32.CryptSignHashW.side_effect = sign_hash
    advapi32.CryptDestroyHash.return_value = True

    with pytest.raises(
        OSError,
        match="Failed to sign with CSP RSA private key",
    ):
        _sign_hash_with_legacy_csp(
            advapi32,
            key_handle=456,
            key_spec=AT_SIGNATURE,
            digest=digest,
        )

    advapi32.CryptDestroyHash.assert_called_once_with(789)


def _create_certificate_context(raw_data: bytes):
    encoded = (ctypes.c_ubyte * len(raw_data))(*raw_data)

    certificate = _CERT_CONTEXT()
    certificate.pbCertEncoded = ctypes.cast(
        encoded,
        ctypes.POINTER(ctypes.c_ubyte),
    )
    certificate.cbCertEncoded = len(encoded)

    return ctypes.pointer(certificate), encoded


def _create_certificate_store_assertion(mocker, *, send_x5c=False):
    crypt32 = mocker.Mock()
    ncrypt = mocker.Mock()
    advapi32 = mocker.Mock()

    certificate, encoded = _create_certificate_context(b"\x01\x02\x03\x04")

    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store." "_load_windows_apis",
        return_value=(crypt32, ncrypt, advapi32),
    )
    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_find_certificate_context",
        return_value=certificate,
    )
    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store." "weakref.finalize"
    )

    assertion = _CertificateStoreClientAssertion(
        subject_name="test-agent",
        store_name="My",
        valid_only=True,
        send_x5c=send_x5c,
        client_id="test-client-id",
    )

    return assertion, crypt32, ncrypt, advapi32, encoded


def _decode_jwt_part(value: str):
    padding = "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(value + padding))


def test_get_certificate_raw_data():
    certificate, _encoded = _create_certificate_context(b"\x01\x02\x03\x04")

    assert _get_certificate_raw_data(certificate) == b"\x01\x02\x03\x04"


@pytest.mark.parametrize(
    ("use_sha2", "expected"),
    [
        (False, "EtraH_9NR4et4zMxRyAsO0Q-N28"),
        (True, "n2SnR-G5fxMfq7a0Rylsm28CAeefs8U1bmx36JtqgGo"),
    ],
)
def test_compute_certificate_thumbprint(use_sha2, expected):
    certificate, _encoded = _create_certificate_context(b"\x01\x02\x03\x04")

    assert _compute_certificate_thumbprint(certificate, use_sha2=use_sha2) == expected


def test_sign_hash_with_cng_pkcs1_returns_signature(mocker):
    ncrypt = mocker.Mock()
    digest = bytes(range(32))
    expected_signature = b"\x01\x02\x03\x04"

    def sign_hash(
        _key_handle,
        _padding_info,
        _digest,
        _digest_size,
        signature,
        _signature_buffer_size,
        result_size,
        _flags,
    ):
        result_size._obj.value = len(expected_signature)

        if signature is not None:
            for index, value in enumerate(expected_signature):
                signature[index] = value

        return 0

    ncrypt.NCryptSignHash.side_effect = sign_hash

    result = _sign_hash_with_cng_pkcs1(
        ncrypt,
        key_handle=123,
        digest=digest,
    )

    assert result == expected_signature
    assert ncrypt.NCryptSignHash.call_count == 2


def test_sign_hash_with_cng_pkcs1_requires_sha256_digest(mocker):
    ncrypt = mocker.Mock()

    with pytest.raises(ValueError, match="SHA-256 digest"):
        _sign_hash_with_cng_pkcs1(
            ncrypt,
            key_handle=123,
            digest=b"invalid",
        )

    ncrypt.NCryptSignHash.assert_not_called()


def test_sign_hash_with_cng_pkcs1_raises_when_signing_fails(mocker):
    ncrypt = mocker.Mock()
    digest = bytes(32)

    def sign_hash(
        _key_handle,
        _padding_info,
        _digest,
        _digest_size,
        signature,
        _signature_buffer_size,
        result_size,
        _flags,
    ):
        if signature is None:
            result_size._obj.value = 256
            return 0

        return 1

    ncrypt.NCryptSignHash.side_effect = sign_hash

    with pytest.raises(
        OSError,
        match="Failed to sign with CNG PKCS#1 private key",
    ):
        _sign_hash_with_cng_pkcs1(
            ncrypt,
            key_handle=123,
            digest=digest,
        )


def test_certificate_store_client_assertion_signs_with_cng(mocker):
    assertion, _crypt32, ncrypt, advapi32, _encoded = (
        _create_certificate_store_assertion(mocker, send_x5c=True)
    )

    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_acquire_private_key",
        return_value=(123, CERT_NCRYPT_KEY_SPEC, True),
    )
    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_is_private_key_rsa",
        return_value=True,
    )
    sign_cng = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_sign_hash_with_cng",
        return_value=b"\x01\x02\x03\x04",
    )
    sign_legacy = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_sign_hash_with_legacy_csp"
    )
    release_key = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_release_private_key"
    )
    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store.time.time",
        return_value=1000,
    )
    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store.uuid.uuid4",
        return_value=uuid.UUID("12345678-1234-5678-1234-567812345678"),
    )

    assertion.bind_audience("https://login.example/token")

    result = assertion()
    encoded_header, encoded_payload, encoded_signature = result.split(".")

    assert _decode_jwt_part(encoded_header) == {
        "alg": "PS256",
        "typ": "JWT",
        "x5t#S256": "n2SnR-G5fxMfq7a0Rylsm28CAeefs8U1bmx36JtqgGo",
        "x5c": "AQIDBA==",
    }
    assert _decode_jwt_part(encoded_payload) == {
        "aud": "https://login.example/token",
        "iss": "test-client-id",
        "sub": "test-client-id",
        "nbf": "1000",
        "exp": "1600",
        "jti": "12345678-1234-5678-1234-567812345678",
    }

    expected_digest = hashlib.sha256(
        f"{encoded_header}.{encoded_payload}".encode("ascii")
    ).digest()

    sign_cng.assert_called_once_with(
        ncrypt,
        key_handle=123,
        digest=expected_digest,
    )
    sign_legacy.assert_not_called()

    assert (
        base64.urlsafe_b64decode(
            encoded_signature + "=" * (-len(encoded_signature) % 4)
        )
        == b"\x01\x02\x03\x04"
    )

    release_key.assert_called_once_with(
        ncrypt,
        advapi32,
        key_handle=123,
        key_spec=CERT_NCRYPT_KEY_SPEC,
        caller_free=True,
    )


def test_certificate_store_client_assertion_signs_with_legacy_csp(mocker):
    assertion, _crypt32, ncrypt, advapi32, _encoded = (
        _create_certificate_store_assertion(mocker)
    )

    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_acquire_private_key",
        return_value=(456, AT_SIGNATURE, False),
    )
    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_is_private_key_rsa",
        return_value=True,
    )
    sign_cng = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store." "_sign_hash_with_cng"
    )
    sign_legacy = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_sign_hash_with_legacy_csp",
        return_value=b"\x05\x06\x07\x08",
    )
    release_key = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_release_private_key"
    )

    assertion.bind_audience("https://login.example/token")

    result = assertion()
    encoded_header, encoded_payload, _encoded_signature = result.split(".")

    assert _decode_jwt_part(encoded_header) == {
        "alg": "RS256",
        "typ": "JWT",
        "x5t": "EtraH_9NR4et4zMxRyAsO0Q-N28",
    }

    expected_digest = hashlib.sha256(
        f"{encoded_header}.{encoded_payload}".encode("ascii")
    ).digest()

    sign_legacy.assert_called_once_with(
        advapi32,
        key_handle=456,
        key_spec=AT_SIGNATURE,
        digest=expected_digest,
    )
    sign_cng.assert_not_called()

    release_key.assert_called_once_with(
        ncrypt,
        advapi32,
        key_handle=456,
        key_spec=AT_SIGNATURE,
        caller_free=False,
    )


def test_certificate_store_client_assertion_requires_audience(mocker):
    assertion, _crypt32, _ncrypt, _advapi32, _encoded = (
        _create_certificate_store_assertion(mocker)
    )

    with pytest.raises(
        RuntimeError,
        match="audience has not been initialized",
    ):
        assertion()


def test_certificate_store_client_assertion_rejects_non_rsa_key(mocker):
    assertion, _crypt32, ncrypt, advapi32, _encoded = (
        _create_certificate_store_assertion(mocker)
    )

    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_acquire_private_key",
        return_value=(123, CERT_NCRYPT_KEY_SPEC, True),
    )
    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_is_private_key_rsa",
        return_value=False,
    )
    release_key = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_release_private_key"
    )

    assertion.bind_audience("https://login.example/token")

    with pytest.raises(ValueError, match="certificate is not of type RSA"):
        assertion()

    release_key.assert_called_once_with(
        ncrypt,
        advapi32,
        key_handle=123,
        key_spec=CERT_NCRYPT_KEY_SPEC,
        caller_free=True,
    )


def test_certificate_store_client_assertion_falls_back_to_cng_pkcs1(mocker):
    assertion, _crypt32, ncrypt, advapi32, _encoded = (
        _create_certificate_store_assertion(mocker, send_x5c=True)
    )

    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_acquire_private_key",
        return_value=(123, CERT_NCRYPT_KEY_SPEC, True),
    )
    mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_is_private_key_rsa",
        return_value=True,
    )
    sign_cng = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_sign_hash_with_cng",
        side_effect=OSError("Failed to sign with CNG private key."),
    )
    sign_pkcs1 = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_sign_hash_with_cng_pkcs1",
        return_value=b"\x01\x02\x03\x04",
    )
    sign_legacy = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_sign_hash_with_legacy_csp"
    )
    release_key = mocker.patch(
        "microsoft_agents.authentication.msal._certificate_store."
        "_release_private_key"
    )

    assertion.bind_audience("https://login.example/token")

    result = assertion()
    encoded_header, encoded_payload, _encoded_signature = result.split(".")

    assert _decode_jwt_part(encoded_header) == {
        "alg": "RS256",
        "typ": "JWT",
        "x5t": "EtraH_9NR4et4zMxRyAsO0Q-N28",
        "x5c": "AQIDBA==",
    }

    expected_digest = hashlib.sha256(
        f"{encoded_header}.{encoded_payload}".encode("ascii")
    ).digest()

    sign_cng.assert_called_once()
    sign_pkcs1.assert_called_once_with(
        ncrypt,
        key_handle=123,
        digest=expected_digest,
    )
    sign_legacy.assert_not_called()

    release_key.assert_called_once_with(
        ncrypt,
        advapi32,
        key_handle=123,
        key_spec=CERT_NCRYPT_KEY_SPEC,
        caller_free=True,
    )
