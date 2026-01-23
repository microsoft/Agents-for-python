# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from copy import deepcopy

def expand(data: dict, level_sep: str = ".") -> dict:
    """Expand a (partially) flattened dictionary into a nested dictionary.
    Keys with dots (.) are treated as paths representing nested dictionaries.
    
    :param data: The (partially) flattened dictionary to expand.
    :return: The expanded nested dictionary.
    """

    if not isinstance(data, dict):
        return data

    new_data = {}

    # flatten
    for key, value in data.items():
        if level_sep in key:
            index = key.index(level_sep)
            root = key[:index]
            path = key[index + 1 :]

            if root in new_data and path in new_data[root]:
                raise RuntimeError()
            elif root in new_data and not isinstance(new_data[root], (dict, list)):
                raise RuntimeError()

            if root not in new_data:
                new_data[root] = {}

            new_data[root][path] = value

        else:
            root = key
            if root in new_data:
                raise RuntimeError()

            new_data[root] = value

    # expand
    for key, value in new_data.items():
        new_data[key] = expand(value, level_sep=level_sep)

    return new_data

def _merge(original: dict, other: dict, overwrite_leaves: bool = True) -> None:

    """Merge two dictionaries recursively.

    :param a: The first dictionary.
    :param b: The second dictionary.
    :param overwrite_leaves: Whether to overwrite leaf values in the first dictionary with those from the second.
    :return: The merged dictionary. If false, only missing keys in the first dictionary are added from the second.
    """

    for key in other.keys():
        if key not in original:
            original[key] = other[key]
        elif isinstance(original[key], dict) and isinstance(other[key], dict):
            merge(original[key], other[key], overwrite_leaves=overwrite_leaves)
        elif not isinstance(original[key], dict) and overwrite_leaves:
            original[key] = other[key]

def _resolve_kwargs(data: dict | None = None, **kwargs) -> dict:

    """Combine a dictionary and keyword arguments into a single dictionary.

    :param data: An optional dictionary.
    :param kwargs: Additional keyword arguments.
    :return: A combined dictionary.
    """

    new_data = deepcopy(data or {})
    kdict = {**kwargs}
    _merge(new_data, kdict, overwrite_leaves=True)
    return new_data

def deep_update(original: dict, updates: dict | None = None, **kwargs) -> None:
    """Update a dictionary with new values.

    :param original: The original dictionary to update.
    :param updates: The dictionary containing new values.
    """

    updates = _resolve_kwargs(updates, **kwargs)
    _merge(original, updates, overwrite_leaves=True)

def set_defaults(original: dict, defaults: dict | None = None, **kwargs) -> None:
    """Set default values in a dictionary.

    :param original: The original dictionary to populate.
    :param defaults: The dictionary containing default values.
    """
    defaults = _resolve_kwargs(defaults, **kwargs)
    _merge(original, defaults, overwrite_leaves=False)