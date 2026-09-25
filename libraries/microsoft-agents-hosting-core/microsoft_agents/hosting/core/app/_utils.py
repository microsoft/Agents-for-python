# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from email.message import Message
from urllib.parse import urlparse

_CONTENT_TYPE = "Content-Type"


def _parse_content_type(content_type: str) -> tuple[str, dict[str, str]] | None:
    """Parses the given content type string into its main type and parameters.

    :param content_type: The content type string to parse.
    :return: A tuple containing the main content type and a dictionary of parameters,
             or None if parsing fails.
    """
    email = Message()
    email[_CONTENT_TYPE] = content_type
    params = email.get_params()
    if params is None:
        return None
    # the first param is the mime-type
    # the later ones are the attributes like "charset"
    return params[0][0], dict(params[1:])


def _basic_url_check(url: str) -> bool:
    """Performs a basic check to see if the given string is a valid URL.

    :param url: The URL string to check.
    :return: True if the URL has a valid scheme and netloc, False otherwise.
    """
    parsed = urlparse(url)
    return parsed.scheme == "https" or (
        parsed.scheme == "http" and parsed.hostname == "localhost"
    )
