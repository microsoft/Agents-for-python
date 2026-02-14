# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import platform


class UserAgentHelper:
    """
    Helper class for generating user agent headers.
    """

    CLIENT_NAME = "CopilotStudioClient"
    CLIENT_VERSION = "0.8.0"  # Should match package version

    @staticmethod
    def get_user_agent_header() -> str:
        """
        Generate a user agent header string.

        :return: User agent header string in the format:
                 "ClientName.agents-sdk-python/version Python/version OS/version"
        """
        # Get Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Get OS information
        os_name = platform.system()
        os_version = platform.release()

        # Construct user agent string
        user_agent = (
            f"{UserAgentHelper.CLIENT_NAME}.agents-sdk-python/{UserAgentHelper.CLIENT_VERSION} "
            f"Python/{python_version} "
            f"{os_name}/{os_version}"
        )

        return user_agent
