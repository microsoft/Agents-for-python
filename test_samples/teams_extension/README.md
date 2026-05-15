# Teams Extension Samples

These samples exercise `TeamsAgentExtension` after its model layer was switched
to use the Teams SDK Pydantic models from
[`microsoft-teams-api`](https://pypi.org/project/microsoft-teams-api/) (the
`microsoft_teams.api.models` namespace from
[microsoft/teams.py](https://github.com/microsoft/teams.py)).

They mirror the AgentApplication-based samples added in
[microsoft/Agents-for-net PR #740](https://github.com/microsoft/Agents-for-net/pull/740),
adapted to Python decorators on `TeamsAgentExtension` sub-objects.

## Samples

| File | What it shows |
| --- | --- |
| `message_extensions_agent.py` | `composeExtension/*` invokes — search query, select item, submit action, query link, settings URL, configure settings, fetch task. |
| `task_modules_agent.py` | `task/fetch` and `task/submit` for simple form, webpage dialog, and a multi-step (chained submits) flow. |
| `meeting_events_agent.py` | Meeting start/end via the new single `MeetingDetails` model, plus participant join/leave and read receipts (legacy models retained). |
| `targeted_messages_agent.py` | Group-chat targeted-message fan-out mirroring [microsoft/Agents-for-net PR #807](https://github.com/microsoft/Agents-for-net/pull/807). Iterates chat members via `TeamsInfo.get_paged_members`, builds a per-member `Activity` with explicit `recipient` plus an `activityTreatment=targeted` entity, and sends through `adapter.send_activities` directly to bypass `TurnContext.apply_conversation_reference` (which would otherwise overwrite the recipient). See the module docstring for the limitations of this inline workaround. |

## Setup

From the repo root:

```bash
. ./scripts/dev_setup.sh        # or scripts/dev_setup.ps1 on Windows
pip install microsoft-teams-api  # only-binary may be needed on Windows: pip install --only-binary=:all: microsoft-teams-api
cp test_samples/teams_extension/env.TEMPLATE test_samples/teams_extension/.env
# Fill in CLIENTID / CLIENTSECRET / TENANTID in the .env
```

## Run

```bash
cd test_samples/teams_extension
python message_extensions_agent.py
# or
python task_modules_agent.py
# or
python meeting_events_agent.py
# or
python targeted_messages_agent.py
```

The agent listens on `http://localhost:3978/api/messages`. To exercise the
invoke-style routes (message extension queries, task modules) point the
[Microsoft 365 Agents Playground](https://learn.microsoft.com/en-us/microsoft-365/agents-sdk/test-with-toolkit-project)
or a Teams app manifest at the tunnel endpoint.

## Notes on the Teams SDK model swap

* `MeetingStartEventDetails` and `MeetingEndEventDetails` collapse to a single
  `MeetingDetails` from `microsoft_teams.api.models` — `meeting.on_start` and
  `meeting.on_end` both deserialize to that one type.
* `MeetingParticipantsEventDetails` and `ReadReceiptInfo` have no Teams SDK
  equivalents and continue to ship from `microsoft_agents.activity.teams`.
* `MessagingExtensionAction.command_context` is **required** in the Teams SDK
  model (it was optional previously). Real Teams activities always include it
  per the platform contract; mock fixtures may need to add it.
