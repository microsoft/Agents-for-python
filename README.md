# Microsoft 365 Agents SDK - Python

![Build Status](https://github.com/microsoft/Agents-for-python/actions/workflows/python-package.yml/badge.svg)
![PyPI Downloads](https://img.shields.io/pypi/dm/microsoft-agents-activity)

The Microsoft 365 Agent SDK simplifies building full stack, multichannel, trusted agents for platforms including M365, Teams, Copilot Studio, and Webchat. We also offer integrations with 3rd parties such as Facebook Messenger, Slack, or Twilio. The SDK provides developers with the building blocks to create agents that handle user interactions, orchestrate requests, reason responses, and collaborate with other agents.

The M365 Agent SDK is a comprehensive framework for building enterprise-grade agents, enabling developers to integrate components from the Azure AI Foundry SDK, Semantic Kernel, as well as AI components from other vendors.

For more information please see the parent project information here [Microsoft 365 Agents SDK](https://aka.ms/agents)

## Getting Started

The best way to get started with these packages is to look at the samples available in [https://github.com/microsoft/Agents](https://github.com/microsoft/Agents)

## Important Notice - Import Changes

> **⚠️ Breaking Change**: Recent updates have changed the Python import structure from `microsoft.agents` to `microsoft_agents` (using underscores instead of dots). Please update your imports accordingly.

### Import Examples

```python
# Activity types and models
from microsoft_agents.activity import Activity

# Core hosting functionality
from microsoft_agents.hosting.core import TurnContext

# aiohttp hosting
from microsoft_agents.hosting.aiohttp import start_agent_process

# Teams-specific functionality (compatible only with activity handler)
from microsoft_agents.hosting.teams import TeamsActivityHandler

# Azure Blob storage
from microsoft_agents.storage.blob import BlobStorage

# CosmosDB storage
from microsoft_agents.storage.cosmos import CosmosDbStorage

# MSAL authentication
from microsoft_agents.authentication.msal import MsalAuth

# Copilot Studio client
from microsoft_agents.copilotstudio.client import CopilotClient
```

## Packages Overview

We offer the following PyPI packages to create conversational experiences based on Agents:

| Package Name | PyPI Version | Description | Replaces |
|--------------|-------------|-------------|----------|
| `microsoft-agents-activity` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-activity)](https://pypi.org/project/microsoft-agents-activity/) | Types and validators implementing the Activity protocol spec. | `botframework-schema` |
| `microsoft-agents-hosting-core` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-core)](https://pypi.org/project/microsoft-agents-hosting-core/) | Core library for Microsoft Agents hosting. | `botbuilder-core, botframework-connector` |
| `microsoft-agents-hosting-aiohttp` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-aiohttp)](https://pypi.org/project/microsoft-agents-hosting-aiohttp/) | Configures aiohttp to run the Agent. | `botbuilder-integration-aiohttp` |
| `microsoft-agents-hosting-teams` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-teams)](https://pypi.org/project/microsoft-agents-hosting-teams/) | Provides classes to host an Agent for Teams. | N/A |
| `microsoft-agents-storage-blob` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-blob)](https://pypi.org/project/microsoft-agents-storage-blob/) | Extension to use Azure Blob as storage. | `botbuilder-azure` |
| `microsoft-agents-storage-cosmos` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-cosmos)](https://pypi.org/project/microsoft-agents-storage-cosmos/) | Extension to use CosmosDB as storage. | `botbuilder-azure` |
| `microsoft-agents-authentication-msal` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-msal)](https://pypi.org/project/microsoft-agents-authentication-msal/) | MSAL-based authentication for Microsoft Agents. | N/A |

Additionally we provide a Copilot Studio Client, to interact with Agents created in CopilotStudio:

| Package Name | PyPI Version | Description |
|--------------|-------------|-------------|
| `microsoft-agents-copilotstudio-client` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-copilotstudio-client)](https://pypi.org/project/microsoft-agents-copilotstudio-client/) | Direct to Engine client to interact with Agents created in CopilotStudio |

### Environment requirements

The packages should target Python 3.9 or greater, and can be used with modern Python package managers like pip, poetry, or conda.

> Note: We recommend using Python 3.11 or later for optimal performance and compatibility with all features.

### Debugging

The packages include source code to allow debugging in your preferred Python IDE or debugger.

### Code Style

We are using `black` and `flake8` for code formatting and linting.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
