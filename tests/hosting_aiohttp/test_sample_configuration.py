# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import importlib.util
import os
import sys
from pathlib import Path

import pytest

from microsoft_agents.activity.config import Configuration

_SAMPLES = Path(__file__).resolve().parents[2] / "test_samples"


@pytest.fixture(
    params=[
        r"agentic-test\src\start_server.py",
        r"app_style\shared\start_server.py",
        r"cards\start_server.py",
        r"extensions\extension-starter\src\sample\start_server.py",
        r"extensions\slack-agent\src\start_server.py",
        r"hosting_msteams\conversation-agent\src\start_server.py",
        r"hosting_msteams\graph-clients\src\start_server.py",
        r"hosting_msteams\message-extensions\src\start_server.py",
        r"hosting_msteams\task-modules\src\start_server.py",
        r"otel\quickstart\src\start_server.py",
        r"otel\zero-code\src\start_server.py",
        r"teams_extension\shared\start_server.py",
        r"testing\src\start_server.py",
        r"tethered-agent\src\start_server.py",
    ]
)
def sample_server(request, monkeypatch):
    sample_path = _SAMPLES.joinpath(*request.param.split("\\"))
    module_name = "_sample_configuration_server"
    spec = importlib.util.spec_from_file_location(
        module_name,
        sample_path,
        submodule_search_locations=[str(sample_path.parent)],
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    yield module
    for name in list(sys.modules):
        if name.startswith(module_name + "."):
            del sys.modules[name]


@pytest.mark.parametrize("port", [None, "4123"])
def test_sample_server_passes_root_configuration(sample_server, mocker, port):
    config = Configuration(
        {
            "PORT": port,
            "TOKENVALIDATION": {"AUDIENCES": ["sample-client"]},
            "AGENTAPPLICATION": {"USERAUTHORIZATION": {"HANDLERS": {}}},
        }
    )
    application = mocker.patch.object(sample_server, "Application").return_value
    run_app = mocker.patch.object(sample_server, "run_app")
    agent, adapter = object(), object()

    sample_server.start_server(agent, adapter, config=config)

    assigned = {
        call.args[0]: call.args[1] for call in application.__setitem__.call_args_list
    }
    assert assigned["agent_configuration"] is config
    assert assigned["adapter"] is adapter
    assert agent in assigned.values()
    run_app.assert_called_once_with(
        application, host="localhost", port=3978 if port is None else 4123
    )


@pytest.mark.parametrize("enabled", [None, "true", "false"])
def test_sidecar_sample_reads_nested_token_validation(mocker, enabled):
    settings = {
        "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID": "sample-client",
        "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID": "sample-tenant",
    }
    if enabled is not None:
        settings["TOKENVALIDATION__ENABLED"] = enabled
    mocker.patch.dict(os.environ, settings, clear=True)
    mocker.patch("dotenv.load_dotenv", return_value=False)
    spec = importlib.util.spec_from_file_location(
        "_sidecar_sample_configuration", _SAMPLES / "entra_sidecar" / "agent.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    application = mocker.patch.object(module, "Application")
    mocker.patch.object(module, "run_app")

    module.start_server(module.AGENT_APP, module.ADAPTER)

    assert module.TOKEN_VALIDATION_ENABLED is (enabled == "true")
    application.assert_called_once_with(
        middlewares=[
            (
                module.jwt_authorization_middleware
                if enabled == "true"
                else module._anonymous_auth_middleware
            )
        ]
    )
    application.return_value.__setitem__.assert_any_call(
        "agent_configuration", module.agents_sdk_config
    )
