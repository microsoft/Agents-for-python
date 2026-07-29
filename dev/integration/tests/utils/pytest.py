# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import pytest
from dotenv import dotenv_values

def skip_if_no_var(*env_vars: str, environ: dict | None = None, load_root_env_file: bool = False):
    """Skip the test if any of the specified environment variables are not set.

    :param env_vars: The environment variable names to check.
    :param environ: Optional dictionary representing the environment variables. Defaults to os.environ.
    :return: A pytest mark to skip the test if any environment variable is not set.
    """
    if load_root_env_file:
        # Load environment variables from the root .env file if specified
        environ = {**os.environ, **dotenv_values(".env")}
    return pytest.mark.skipif(
        any(env_var not in (environ or os.environ) for env_var in env_vars),
        reason=f"Skipping test because one or more environment variables are not set: {', '.join(env_vars)}"
    )