# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .start_server import create_app, start_server

app = create_app()


if __name__ == "__main__":
    start_server(app)
