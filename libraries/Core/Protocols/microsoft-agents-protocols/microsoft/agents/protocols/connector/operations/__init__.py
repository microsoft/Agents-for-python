# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator (autorest: 3.10.3, generator: @autorest/python@6.27.0)
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------
# pylint: disable=wrong-import-position

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._connector_operations_async_patch import *  # pylint: disable=unused-wildcard-import

from ._connector_operations_async import AttachmentsOperations  # type: ignore
from ._connector_operations_async import ConversationsOperations  # type: ignore
from ._connector_operations_async import ConnectorInternalsOperations  # type: ignore

from ._connector_operations_async_patch import __all__ as _patch_all
from ._connector_operations_async_patch import *
from ._connector_operations_async_patch import patch_sdk as _patch_sdk

__all__ = [
    "AttachmentsOperations",
    "ConversationsOperations",
    "ConnectorInternalsOperations",
]
__all__.extend([p for p in _patch_all if p not in __all__])  # pyright: ignore
_patch_sdk()
