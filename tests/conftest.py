# content of conftest.py

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-cosmos", action="store_true", default=False, help="run CosmosDB tests"
    )
    parser.addoption(
        "--run-blob", action="store_true", default=False, help="run Blob Storage tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "cosmos: mark test as CosmosDB test")
    config.addinivalue_line("markers", "blob: mark test as Blob Storage test")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-cosmos"):
        skip_cosmos = pytest.mark.skip(reason="need --run-cosmos option to run")
        for item in items:
            if "cosmos" in item.keywords:
                item.add_marker(skip_cosmos)
    if not config.getoption("--run-blob"):
        skip_blob = pytest.mark.skip(reason="need --run-blob option to run")
        for item in items:
            if "blob" in item.keywords:
                item.add_marker(skip_blob)