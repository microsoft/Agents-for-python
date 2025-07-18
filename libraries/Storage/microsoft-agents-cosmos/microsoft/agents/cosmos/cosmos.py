# # Copyright (c) Microsoft Corporation. All rights reserved.
# # Licensed under the MIT License.

# import json

# from typing import TypeVar
# from threading import Lock
# from hashlib import sha256

# from azure.core.auth import (
#     StorageSharedKeyCredential,
#     TokenCredential,
#     AnonymousCredential,
# )

# from azure.cosmos import (
#     documents,
#     http_constants,
#     CosmosDict,
# )
# from azure.cosmos.aio import (
#     ContainerProxy,
#     CosmosClient,
#     DatabaseProxy,
# )
# import azure.cosmos.exceptions as cosmos_exceptions

# from microsoft.agents.storage import Storage, StoreItem
# from microsoft.agents.storage._type_aliases import JSON
# from microsoft.agents.storage.error_handling import ignore_error, is_status_code_error

# StoreItemT = TypeVar("StoreItemT", bound=StoreItem)

# class CosmosDBStorage(Storage):
#     """A CosmosDB based storage provider using partitioning"""

#     def __init__(self, config: CosmosDBConfig):
#         """Create the storage object.

#         :param config:
#         """
#         super().__init__()

#         CosmosDBStorage._validate_config(config)

#         self._config: CosmosDBConfig = config
#         self._client: CosmosClient = self._create_client()
#         self._database: DatabaseProxy = None
#         self._container: ContainerProxy = None
#         self._compatability_mode_partition_key: bool = False
#         # Lock used for synchronizing container creation
#         self._lock: Lock = Lock()

#     @staticmethod
#     def _validate_config(config: CosmosDBConfig):
#         if not config:
#             raise ValueError("CosmosDBStorage: CosmosDBConfig is required.")
#         if not config.cosmos_db_endpoint:
#             raise ValueError("CosmosDBStorage: cosmos_db_endpoint is required.")
#         if not config.auth_key:
#             raise ValueError("CosmosDBStorage: auth_key is required.")
#         if not config.database_id:
#             raise ValueError("CosmosDBStorage: database_id is required.")
#         if not config.container_id:
#             raise ValueError("CosmosDBStorage: container_id is required.")

#     @staticmethod
#     def _validate_suffix(config: CosmosDBConfig):

#         if config.key_suffix:
#             if config.compatibility_mode:
#                 raise ValueError(
#                     "compatibilityMode cannot be true while using a keySuffix."
#                 )
#             suffix_escaped: str = sanitize_key(config.key_suffix)
#             if suffix_escaped != config.key_suffix:
#                 raise ValueError(
#                     f"Cannot use invalid Row Key characters: {config.key_suffix} in keySuffix."
#                 )
            
#     def _create_client(self) -> CosmosClient:

#         if self._config.url:
#             if not self._config.credential:
#                 raise ValueError(
#                     "CosmosDBStorage: Credential is required when using a custom service URL."
#                 )
#             return CosmosClient(account_url=self._config.url, credential=self._config.credential)
#         else:

#         connection_policy = self._config.cosmos_client_options.get(
#             "connection_policy", documents.ConnectionPolicy()
#         )

#         # kwargs 'connection_verify' is to handle CosmosClient overwriting the
#         # ConnectionPolicy.DisableSSLVerification value.
#         return CosmosClient(
#             self._config.cosmos_db_endpoint,
#             self._config.auth_key,
#             self._config.cosmos_client_options.get("consistency_level", None),
#             **{
#                 "connection_policy": connection_policy,
#                 "connection_verify": not connection_policy.DisableSSLVerification,
#             },
#         )

#     async def _read_item(key: str) -> tuple[str, StoreItemT]:
#         escaped_key: str = sanitize_key(
#             key, self._config.key_suffix, self._config.compatibility_mode
#         )
#         read_item_response: CosmosDict = await self._container.read_item(
#             escaped_key, self._get_partition_key(escaped_key)
#         )
#         doc: JSON = read_item_response.get("document")
#         return read_item_response["realId"], target_cls.from_json_to_store_item(doc)

#     async def _write_item(key: str, item: StoreItem) -> None:
#         doc = {
#             "id": sanitize_key(
#                 key, self._config.key_suffix, self._config.compatibility_mode
#             ),
#             "realId": key,
#             "document": item.store_item_to_json(),
#         }
#         await self._container.upsert_item(body=doc)

#     async def _delete_item(self, key: str) -> None:
#         escaped_key: str = sanitize_key(
#             key, self._config.key_suffix, self._config.compatibility_mode
#         )
#         await ignore_error(self._container.delete_item(
#             escaped_key, self._get_partition_key(escaped_key)
#         ), is_status_code_error(404))

#     async def initialize(self) -> None:
#         if not self._container:
#             with self._lock:
#                 # in case another thread attempted to initialize just before acquiring the lock
#                 if self._container: return

#                 if not self._database:
#                     self._database = self._client.create_database_if_not_exists(
#                         self._config.database_id
#                     )

#                 partition_key = {
#                     "paths": ["/id"],
#                     "kind": documents.PartitionKind.Hash,
#                 }
#                 try:
#                     self._container = self._database.create_container(
#                         self._config.container_id,
#                         partition_key,
#                         offer_throughput=self._config.container_throughput,
#                     )
#                 except cosmos_exceptions.CosmosHttpResponseError as err:
#                     if err.status_code == http_constants.StatusCodes.CONFLICT:
#                         self._container = self._database.get_container_client(
#                             self._config.container_id
#                         )
#                         properties = self._container.read()
#                         if "partitionKey" not in properties:
#                             self._compatability_mode_partition_key = True
#                         else:
#                             paths = properties["partitionKey"]["paths"]
#                             if "/partitionKey" in paths:
#                                 self._compatability_mode_partition_key = True
#                             elif "/id" not in paths:
#                                 raise Exception(
#                                     f"Custom Partition Key Paths are not supported. {self._config.container_id} "
#                                     "has a custom Partition Key Path of {paths[0]}."
#                                 )
#                     else:
#                         raise err

#     def _get_partition_key(self, key: str) -> str:
#         return "" if self._compatability_mode_partition_key else key
