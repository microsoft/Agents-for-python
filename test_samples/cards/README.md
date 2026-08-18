# Cards sample

This sample ports the .NET cards sample to the Python `AgentApplication`
AdaptiveCard system. It demonstrates:

- Adaptive Card `Action.Submit`
- Adaptive Card `Action.Execute`
- Adaptive Card dynamic search with `Data.Query`
- Hero, thumbnail, audio, video, animation, and receipt cards

`Action.Execute` and dynamic search require Microsoft Teams.
Dynamic search filters a catalog of Microsoft Agents SDK packages and retrieves
their current metadata from PyPI's project JSON API.

## Run

1. Copy `env.TEMPLATE` to `.env` and configure the service connection.
2. From this directory, run:

   ```pwsh
   python agent.py
   ```

3. Configure the Azure Bot messaging endpoint as
   `https://<your-dev-tunnel>/api/messages`.

Send any message to display the command card. Available commands are
`static_submit`, `dynamic_search`, `action_execute`, `hero`, `thumbnail`,
`audio`, `video`, `animation`, and `receipt`.
