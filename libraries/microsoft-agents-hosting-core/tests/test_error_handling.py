import pytest
from microsoft.agents.hosting.core.storage.error_handling import (
    ignore_error,
    is_status_code_error,
)


class CustomError(Exception):
    def __init__(self, status_code: int):
        self.status_code = status_code


async def raise_custom_error(code: int):
    raise CustomError(code)


@pytest.mark.asyncio
async def test_ignore_error_without_error():

    async def func():
        return 42

    assert await ignore_error(func(), lambda e: False) == 42
    assert await ignore_error(func(), lambda e: True) == 42


@pytest.mark.asyncio
async def test_ignore_error_with_error():
    with pytest.raises(CustomError):
        await ignore_error(raise_custom_error(500), lambda e: False)


@pytest.mark.asyncio
async def test_ignore_error_with_ignored_error():
    assert await ignore_error(raise_custom_error(500), lambda e: True) is None


@pytest.mark.asyncio
async def test_is_status_code_with_status_code_check():

    async def func():
        return 42

    assert await ignore_error(func(), is_status_code_error(404)) == 42
    assert (
        await ignore_error(raise_custom_error(403), is_status_code_error(403)) is None
    )

    with pytest.raises(CustomError) as err:
        assert (
            await ignore_error(raise_custom_error(404), is_status_code_error(500))
            is None
        )

    assert err.value.status_code == 404

    async def raise_exception():
        raise Exception()

    with pytest.raises(Exception):
        await ignore_error(raise_exception, is_status_code_error(404))
