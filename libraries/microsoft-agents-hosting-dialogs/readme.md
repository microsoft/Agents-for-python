# Microsoft Agents Hosting - Dialogs

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-dialogs)](https://pypi.org/project/microsoft-agents-hosting-dialogs/)

Dialog system for the Microsoft 365 Agents SDK. Provides waterfall dialogs, prompts, choice recognition, and multi-turn conversation management.

This library is a port of the botbuilder-dialogs library to the new Microsoft 365 Agents SDK. It provides the same dialog primitives (WaterfallDialog, ComponentDialog, DialogSet, DialogContext) and prompts (TextPrompt, NumberPrompt, ChoicePrompt, ConfirmPrompt, DateTimePrompt, OAuthPrompt, etc.) with updated imports and patterns for the new SDK.

## What is this?

This library is part of the **Microsoft 365 Agents SDK for Python** - a comprehensive framework for building enterprise-grade conversational AI agents. The dialogs library enables developers to structure multi-turn conversations with reusable, composable dialog primitives.

## Release Notes

<table style="width:100%">
  <tr>
    <th style="width:20%">Version</th>
    <th style="width:20%">Date</th>
    <th style="width:60%">Release Notes</th>
  </tr>
  <tr>
    <td>1.3.0</td>
    <td>2026-07-30</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v130">
        1.3.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>1.2.0</td>
    <td>2026-07-17</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v120">
        1.2.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>1.1.0</td>
    <td>2026-06-19</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v110">
        1.1.0 Release Notes
      </a>
    </td>
  </tr>
  <tr>
    <td>1.0.0</td>
    <td>2026-05-22</td>
    <td>
      <a href="https://github.com/microsoft/Agents-for-python/blob/main/changelog.md#microsoft-365-agents-sdk-for-python---release-notes-v100">
        1.0.0 Release Notes
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
| `microsoft-agents-hosting-fastapi` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-fastapi)](https://pypi.org/project/microsoft-agents-hosting-fastapi/) | Configures fastapi to run the Agent. |
| `microsoft-agents-hosting-msteams` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-msteams)](https://pypi.org/project/microsoft-agents-hosting-msteams/) | Provides classes to host an Agent for Teams. |
| `microsoft-agents-hosting-dialogs` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-dialogs)](https://pypi.org/project/microsoft-agents-hosting-dialogs/) | Dialog system with waterfall dialogs, prompts, and multi-turn conversation management. |
| `microsoft-agents-hosting-slack` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-hosting-slack)](https://pypi.org/project/microsoft-agents-hosting-slack/) | Provides classes to host an Agent for Slack. |
| `microsoft-agents-storage-blob` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-blob)](https://pypi.org/project/microsoft-agents-storage-blob/) | Extension to use Azure Blob as storage. |
| `microsoft-agents-storage-cosmos` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-storage-cosmos)](https://pypi.org/project/microsoft-agents-storage-cosmos/) | Extension to use CosmosDB as storage. |
| `microsoft-agents-authentication-msal` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-msal)](https://pypi.org/project/microsoft-agents-authentication-msal/) | MSAL-based authentication for Microsoft Agents. |
| `microsoft-agents-authentication-entra-auth-sidecar` | [![PyPI](https://img.shields.io/pypi/v/microsoft-agents-authentication-entra-auth-sidecar)](https://pypi.org/project/microsoft-agents-authentication-entra-auth-sidecar/) | Credential-free Entra ID Agent ID authentication via the sidecar. | 

## Key Features

- **WaterfallDialog**: Sequential step-by-step conversation flows
- **ComponentDialog**: Composable, encapsulated dialog components
- **Prompts**: Built-in prompts for text, numbers, choices, confirmations, dates, attachments, and OAuth
- **Choice recognition**: Locale-aware choice matching and recognition
- **Dialog memory**: Scoped memory management (conversation, user, dialog, class, settings)
- **DialogManager**: High-level dialog orchestration with state management

## Installation

```bash
pip install microsoft-agents-hosting-dialogs
```

## Quick Start

```python
from microsoft_agents.hosting.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogSet,
    DialogTurnStatus,
)
from microsoft_agents.hosting.dialogs.prompts import TextPrompt, PromptOptions
from microsoft_agents.hosting.core import ConversationState, MemoryStorage

storage = MemoryStorage()
conversation_state = ConversationState(storage)
dialog_state = conversation_state.create_property("DialogState")
dialogs = DialogSet(dialog_state)

async def step1(step: WaterfallStepContext):
    return await step.prompt(
        "text_prompt",
        PromptOptions(prompt=MessageFactory.text("What is your name?"))
    )

async def step2(step: WaterfallStepContext):
    await step.context.send_activity(f"Hello, {step.result}!")
    return await step.end_dialog()

dialogs.add(TextPrompt("text_prompt"))
dialogs.add(WaterfallDialog("main", [step1, step2]))
```

