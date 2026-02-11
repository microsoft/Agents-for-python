# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Self-documenting samples for the Microsoft Agents Testing framework.

Each file focuses on one area of the framework and can be run standalone.
Start with ``quickstart.py`` and work through in order.

Samples
-------
quickstart.py
    Minimal example — send a message, print the reply.  Shows
    AiohttpScenario, scenario.client(), and send_expect_replies().

interactive.py
    REPL loop — chat with an in-process agent, print the transcript
    on exit.

scenario_registry_demo.py
    Register, discover, and look up named scenarios with the global
    scenario_registry.  Dot-notation namespacing and glob discovery.

transcript_formatting.py
    Visualise conversations for debugging: ConversationTranscriptFormatter,
    ActivityTranscriptFormatter, DetailLevel, TimeFormat, selectable fields,
    and convenience functions.

pytest_plugin_usage.py
    Zero-boilerplate pytest tests using @pytest.mark.agent_test — class
    and function markers, fixtures (agent_client, agent_environment, etc.),
    registered scenario names, and Select/Expect through the client.

multi_client.py
    Advanced patterns: multiple clients via ClientFactory, per-client
    ActivityTemplate and ClientConfig, child clients with transcript
    scoping, and transcript hierarchy.
"""