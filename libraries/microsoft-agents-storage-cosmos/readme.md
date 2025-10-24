# Microsoft Agents Storage - Cosmos DB

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-storage-cosmos)](https://pypi.org/project/microsoft-agents-storage-cosmos/)

Azure Cosmos DB storage integration for Microsoft 365 Agents SDK. This library provides enterprise-grade persistent storage for conversation state, user data, and custom agent information using Azure Cosmos DB's globally distributed, multi-model database service.

This library implements the storage interface for the Microsoft 365 Agents SDK using Azure Cosmos DB as the backend. It provides automatic partitioning, global distribution, and low-latency access to your agent data. Perfect for production deployments requiring high availability, scalability, and multi-region support.

# What is this?
This library is part of the **Microsoft 365 Agents SDK for Python** - a comprehensive framework for building enterprise-grade conversational AI agents. The SDK enables developers to create intelligent agents that work across multiple platforms including Microsoft Teams, M365 Copilot, Copilot Studio, and web chat, with support for third-party integrations like Slack, Facebook Messenger, and Twilio.

## Release Notes
<table style="width:100%">
  <tr>
    <th style="width:20%">Version</th>
    <th style="width:20%">Date</th>
    <th style="width:60%">Release Notes</th>
  </tr>
  <tr>
    <td>0.5.0</td>
    <td>2025-10-22</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md">
        0.5.0 Release Notes
      </a>
    </td>
  </tr>
</table>

## Packages Overview

We offer the following PyPI packages to create conversational experiences based on Agents:

| Package Name | PyPI Version | Description |
|--------------|-------------|-------------|
| `microsoft-agents-activity` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-activity)](https://pypi.org/project/microsoft-agents-activity/) | Types and validators implementing the Activity protocol spec. |
| `microsoft-agents-hosting-core` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-core)](https://pypi.org/project/microsoft-agents-hosting-core/) | Core library for Microsoft Agents hosting. |
| `microsoft-agents-hosting-aiohttp` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-aiohttp)](https://pypi.org/project/microsoft-agents-hosting-aiohttp/) | Configures aiohttp to run the Agent. |
| `microsoft-agents-hosting-teams` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-teams)](https://pypi.org/project/microsoft-agents-hosting-teams/) | Provides classes to host an Agent for Teams. |
| `microsoft-agents-storage-blob` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-blob)](https://pypi.org/project/microsoft-agents-storage-blob/) | Extension to use Azure Blob as storage. |
| `microsoft-agents-storage-cosmos` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-cosmos)](https://pypi.org/project/microsoft-agents-storage-cosmos/) | Extension to use CosmosDB as storage. |
| `microsoft-agents-authentication-msal` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-msal)](https://pypi.org/project/microsoft-agents-authentication-msal/) | MSAL-based authentication for Microsoft Agents. |

Additionally we provide a Copilot Studio Client, to interact with Agents created in CopilotStudio:

| Package Name | PyPI Version | Description |
|--------------|-------------|-------------|
| `microsoft-agents-copilotstudio-client` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-copilotstudio-client)](https://pypi.org/project/microsoft-agents-copilotstudio-client/) | Direct to Engine client to interact with Agents created in CopilotStudio |

**Why Cosmos DB?**
- 🌍 Global distribution with multi-region writes
- ⚡ Single-digit millisecond latency
- 📈 Automatic and instant scalability
- 🔄 Multiple consistency models
- 💪 99.999% availability SLA

## Installation

```bash
pip install microsoft-agents-storage-cosmos
```


## Environment Setup

### Local Development with Cosmos DB Emulator

Install and run the Azure Cosmos DB Emulator for local testing:

**Download:** [Azure Cosmos DB Emulator](https://docs.microsoft.com/azure/cosmos-db/local-emulator)


## Best Practices

1. **Use Managed Identity in Production** - Avoid storing auth keys in code or environment variables
2. **Initialize Once** - Call `storage.initialize()` during app startup, not per request
3. **Batch Operations** - Read/write multiple items together when possible
4. **Monitor RU Consumption** - Use Azure Monitor to track Request Units usage
5. **Set Appropriate Throughput** - Start with 400 RU/s, scale up based on metrics
6. **Use Session Consistency** - Default consistency level for most scenarios
7. **Implement Retry Logic** - Handle transient failures with exponential backoff
8. **Partition Wisely** - Current implementation uses `/id` partitioning (automatic)
9. **Enable Diagnostics** - Configure Azure diagnostic logs for troubleshooting
10. **Test with Emulator** - Use local emulator for development and testing

## Key Classes Reference

- **`CosmosDBStorage`** - Main storage implementation using Azure Cosmos DB
- **`CosmosDBStorageConfig`** - Configuration settings for connection and behavior
- **`StoreItem`** - Base class for data models (inherit to create custom types)

# Quick Links

- 📦 [All SDK Packages on PyPI](https://pypi.org/search/?q=microsoft-agents)
- 📖 [Complete Documentation](https://aka.ms/agents)
- 💡 [Python Samples Repository](https://github.com/microsoft/Agents/tree/main/samples/python)
- 🐛 [Report Issues](https://github.com/microsoft/Agents-for-python/issues)

# Sample Applications

|Name|Description|README|
|----|----|----|
|Quickstart|Simplest agent|[Quickstart](https://github.com/microsoft/Agents/blob/main/samples/python/quickstart/README.md)|
|Auto Sign In|Simple OAuth agent using Graph and GitHub|[auto-signin](https://github.com/microsoft/Agents/blob/main/samples/python/auto-signin/README.md)|
|OBO Authorization|OBO flow to access a Copilot Studio Agent|[obo-authorization](https://github.com/microsoft/Agents/blob/main/samples/python/obo-authorization/README.md)|
|Semantic Kernel Integration|A weather agent built with Semantic Kernel|[semantic-kernel-multiturn](https://github.com/microsoft/Agents/blob/main/samples/python/semantic-kernel-multiturn/README.md)|
|Streaming Agent|Streams OpenAI responses|[azure-ai-streaming](https://github.com/microsoft/Agents/blob/main/samples/python/azureai-streaming/README.md)|
|Copilot Studio Client|Console app to consume a Copilot Studio Agent|[copilotstudio-client](https://github.com/microsoft/Agents/blob/main/samples/python/copilotstudio-client/README.md)|
|Cards Agent|Agent that uses rich cards to enhance conversation design |[cards](https://github.com/microsoft/Agents/blob/main/samples/python/cards/README.md)|