# Teams Conversation Agent Sample

Python port of the .NET `ConversationAgent` sample
(`src/samples/Teams/ConversationAgent` in microsoft/Agents-for-net), built on
`AgentApplication` + `TeamsAgentExtension`.

## What it demonstrates

Conversation-update and lifecycle events:

| Event | Decorator |
|-------|-----------|
| installation update | `@teams.activity("installationUpdate")` |
| members added / removed | `@teams.conversation_update("membersAdded" / "membersRemoved")` |
| channel created / renamed / deleted | `@teams.channels.created` / `.renamed` / `.deleted` |
| team renamed | `@teams.teams.renamed` |

Message commands (driven by the welcome card buttons, all `@teams.message(...)`):

| Command | Behaviour |
|---------|-----------|
| (any message) | Sends the welcome card. |
| `update` | Updates the triggering card with an incremented counter. |
| `delete` | Deletes the triggering card. |
| `whoami` | Looks up the caller via the Teams API client. |
| `mentionme` | Replies with an Adaptive Card that @-mentions the caller. |
| `atmention` | Replies with a text message that @-mentions the caller. |
| `messageall` | Proactively sends a 1:1 greeting to every team member. |
| `targeted` | Sends a 1:1 message to every member of the conversation. |

Member lookups use `teams.get_teams_api_client(context).conversations.members`,
and proactive messages use `adapter.create_conversation(...)`.

## Running

1. Copy `env.TEMPLATE` to `.env` and fill in your Azure Bot registration
   (`CLIENTID`, `CLIENTSECRET`, `TENANTID`).
2. Install the SDK libraries (see the repository `README.md`).
3. Start the agent:

   ```bash
   python -m src.main
   ```

The server listens on `http://localhost:3978/api/messages`. Expose it with a
dev tunnel and side-load the app manifest into Teams.
