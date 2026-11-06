# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

_IS_ROOT_CONFIG_KEY = "_metadata_is_root_config_"

def _set_root_config(config: dict, is_root: bool) -> None:
    config[_IS_ROOT_CONFIG_KEY] = is_root

def _is_root_config(config: dict) -> bool:
    return config.get(_IS_ROOT_CONFIG_KEY, False)