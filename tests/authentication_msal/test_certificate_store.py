import ctypes

import pytest
from microsoft_agents.authentication.msal._certificate_store import (
    _CERT_CONTEXT,
    CERT_ENCODING,
    CERT_FIND_SUBJECT_STR_W,
    _find_certificate_context,
    _is_certificate_valid,
    _load_windows_apis,
    _normalize_store_name,
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
