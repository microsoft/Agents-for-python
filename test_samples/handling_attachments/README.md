# Handling Attachments

This sample agent demonstrates how to send and receive attachments:

- **Inline attachments** - an image embedded directly in the activity as a base64 data URI.
- **Internet attachments** - an image referenced by an external HTTP(S) URL.
- **Uploaded attachments** (Microsoft Teams only) - an image uploaded to the channel via the connector client and referenced by its attachment URI.
- **Incoming attachments** - files sent by the user are automatically downloaded (via `AttachmentDownloader` and `M365AttachmentDownloader`) and echoed back as an inline attachment.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Microsoft Agents libraries** (from the root of the repository):
   ```bash
   pip install -e libraries/microsoft-agents-activity
   pip install -e libraries/microsoft-agents-hosting-core
   pip install -e libraries/microsoft-agents-authentication-msal
   pip install -e libraries/microsoft-agents-hosting-fastapi
   ```

3. **Configure environment variables:**
   - Copy `env.TEMPLATE` to `.env`
   - Fill in the required configuration values (`CLIENTID`, `CLIENTSECRET`, `TENANTID`)

## Running the sample

Run from the `handling_attachments` sample directory (not from `src/`), so that the `resources/` folder used by the "Inline Attachment" and "Upload Attachment" options can be resolved relative to the current working directory:

```bash
python -m src.main
```

The agent will start on `http://localhost:3978` by default. You can change the port by setting the `PORT` environment variable.

Connect to the agent with the [M365 Agents Playground](https://github.com/OfficeDev/microsoft-365-agents-toolkit) or Microsoft Teams and select one of the options presented by the agent.
