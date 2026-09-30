import ctypes

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
    _find_certificate_context,
    _is_certificate_valid,
    _is_cng_key_rsa,
    _is_legacy_key_rsa,
    _is_private_key_rsa,
    _load_windows_apis,
    _normalize_store_name,
    _release_private_key,
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
        ("invalid-store", "My"),
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
