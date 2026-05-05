# Microsoft Agents Hosting - Dialogs

[![PyPI version](https://img.shields.io/pypi/v/microsoft-agents-hosting-dialogs)](https://pypi.org/project/microsoft-agents-hosting-dialogs/)

Dialog system for the Microsoft 365 Agents SDK. Provides waterfall dialogs, prompts, choice recognition, and multi-turn conversation management.

This library is a port of the botbuilder-dialogs library to the new Microsoft 365 Agents SDK. It provides the same dialog primitives (WaterfallDialog, ComponentDialog, DialogSet, DialogContext) and prompts (TextPrompt, NumberPrompt, ChoicePrompt, ConfirmPrompt, DateTimePrompt, OAuthPrompt, etc.) with updated imports and patterns for the new SDK.

## What is this?

This library is part of the **Microsoft 365 Agents SDK for Python** - a comprehensive framework for building enterprise-grade conversational AI agents. The dialogs library enables developers to structure multi-turn conversations with reusable, composable dialog primitives.

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

## Release Notes

See [CHANGELOG.md](https://github.com/microsoft/Agents/blob/main/CHANGELOG.md) for release history.
