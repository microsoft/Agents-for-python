import pytest

from microsoft_agents.authentication.msal._certificate_store import (
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
