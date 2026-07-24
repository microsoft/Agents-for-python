# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Show environment help.

Displays help information for the .env file and its required variables.

"""

from microsoft_agents.testing.cli.core import Output, pass_output
from .env_group import env_group


@env_group.command("help")
@pass_output
def help(out: Output):
    """Show environment help.

    Displays help information for the .env file and its required variables.

    :param out: CLI output helper.
    """
    out.info(
        "In the current directory, create a new .env file with the following variables defined:"
    )
    out.info("\tCONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=")
    out.info("\tCONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=")
    out.info("\tCONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=")
