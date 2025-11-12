# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
ErrorMessage class for formatting error messages with error codes and help URLs.
"""


class ErrorMessage:
    """
    Represents a formatted error message with error code and help URL.

    This class formats error messages according to the Microsoft Agents SDK pattern:
    - Original error message
    - Error Code: [negative number]
    - Help URL: https://aka.ms/M365AgentsErrorCodes/#[error_code]
    """

    def __init__(
        self,
        message_template: str,
        error_code: int,
    ):
        """
        Initialize an ErrorMessage.

        :param message_template: The error message template (may include format placeholders)
        :type message_template: str
        :param error_code: The error code (should be negative)
        :type error_code: int
        """
        self.message_template = message_template
        self.error_code = error_code
        self.base_url = "https://aka.ms/M365AgentsErrorCodes"

    def format(self, *args, **kwargs) -> str:
        """
        Format the error message with the provided arguments.

        :param args: Positional arguments for string formatting
        :param kwargs: Keyword arguments for string formatting
        :return: Formatted error message with error code and help URL
        :rtype: str
        """
        # Format the main message
        if args or kwargs:
            message = self.message_template.format(*args, **kwargs)
        else:
            message = self.message_template

        # Append error code and help URL
        return (
            f"{message}\n\n"
            f"Error Code: {self.error_code}\n"
            f"Help URL: {self.base_url}/#{self.error_code}"
        )

    def __str__(self) -> str:
        """Return the formatted error message without any arguments."""
        return self.format()

    def __repr__(self) -> str:
        """Return a representation of the ErrorMessage."""
        return f"ErrorMessage(code={self.error_code}, message='{self.message_template[:50]}...')"
