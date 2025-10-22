# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

def _raise_if_none(label: str, **kwargs) -> None:
    """Raises an exception if any of the provided keyword arguments are None.

    :param label: A label to include in the exception message.
    :param kwargs: The keyword arguments to check.
    :raises ValueError: If any of the provided keyword arguments are None.
    """

    none_args = [name for name, value in kwargs.items() if value is None]
    if none_args:
        raise ValueError(
            f"{label}: The following arguments must be set and non-None: {', '.join(none_args)}"
        )

def _raise_if_falsey(label: str, **kwargs) -> None:
    """Raises an exception if any of the provided keyword arguments are falsey.

    :param label: A label to include in the exception message.
    :param kwargs: The keyword arguments to check.
    :raises ValueError: If any of the provided keyword arguments are falsey.
    """

    falsey_args = [name for name, value in kwargs.items() if not value]
    if falsey_args:
        raise ValueError(
            f"{label}: The following arguments must be set and non-falsey (cannot be None or an empty string, for example): {', '.join(falsey_args)}"
        )