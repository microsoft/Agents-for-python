# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from email.message import Message

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
    # the later ones are the attribtues like "charset"
    return params[0][0], dict(params[1:])