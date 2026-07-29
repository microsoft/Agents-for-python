import pytest

from microsoft_agents.hosting.core._utils._service_set import _ServiceSet


class Service:
    pass


class OtherService:
    pass


def test_get_returns_none_for_missing_service():
    services = _ServiceSet()

    assert services.get(Service) is None


def test_has_returns_false_for_missing_service():
    services = _ServiceSet()

    assert not services.has(Service)


def test_set_registers_service_by_type():
    service = Service()
    services = _ServiceSet()

    services.set(Service, service)

    assert services.has(Service)
    assert services.get(Service) is service
    assert not services.has(OtherService)


def test_set_overwrites_existing_service_for_type():
    first = Service()
    second = Service()
    services = _ServiceSet()

    services.set(Service, first)
    services.set(Service, second)

    assert services.get(Service) is second


def test_copy_constructor_copies_registered_services():
    service = Service()
    services = _ServiceSet()
    services.set(Service, service)

    copy = _ServiceSet(services)

    assert copy.get(Service) is service


def test_copy_constructor_does_not_share_state_dictionary():
    service = Service()
    replacement = Service()
    services = _ServiceSet()
    services.set(Service, service)
    copy = _ServiceSet(services)

    services.set(Service, replacement)

    assert copy.get(Service) is service
    assert services.get(Service) is replacement


def test_get_raises_type_error_when_stored_value_does_not_match_key():
    services = _ServiceSet()
    services._state[Service] = OtherService()

    with pytest.raises(
        TypeError,
    ):
        services.get(Service)
