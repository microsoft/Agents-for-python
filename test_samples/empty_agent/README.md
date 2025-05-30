# Empty-Agent

This is a sample of a simple Agent that is hosted on an aiohttp web service.  This Agent is configured to accept a request and echo the text of the request back to the caller.

This Agent Sample is intended to introduce you to the basic operation of the Microsoft 365 Agents SDK messaging loop. It can also be used as the base for a custom Agent you choose to develop.

## Prerequisites

- [Python](https://python.org) version 3.9 or higher

    ```bash
    # determine python version
    python --version
    ```

## Running this sample

1. Open this folder from your IDE or Terminal of preference
2. Check that you have the libraries installed from pypi test and your environment activated as explained in the README from the `test_samples` folder
3. Install required Python dependencies

```sh
pip install -r requirements.txt
```

4. Configure environment variables
   
   Copy the `env.TEMPLATE` file to `.env` and set the required values:
   
   ```sh
   cp env.TEMPLATE .env
   ```
   
   Then edit the `.env` file to add your credentials (if needed). For anonymous mode, you can leave them empty.

5. Start the Python application

```sh
python agent_application.py
```

At this point you should see a message indicating the server is running on port 3978. The agent is ready to accept messages.

### Interact with the bot from the Teams App Test Tool

To interact with the bot you need a chat client, during the install phase we have acquired the `teams-test-app-tool` than can be used to interact with your bot running in `localhost:3978`

> [!Important]
> The test tool only supports anonymous mode, that means without any `clientId`.

1. Start the test tool with 

```bash
npm run test-tool
```

The tool will open a web browser showing the Teams App Test Tool, ready to send messages to your bot.


Refresh the browser to start a new conversation with the Empty agent.

You should see a message from the bot like: `Echo running on Agents SDK version: {version}`


### Interact with the agent with WebChat UI using Azure Bot Service

1. [Create an Azure Bot](https://aka.ms/AgentsSDK-CreateBot)
   - Record the Application ID, the Tenant ID, and the Client Secret for use below
  
1. Configuring the token connection in the Agent settings
    1. Open the `env.TEMPLATE` file in the root of the sample project, rename it to `.env` and configure the following values:
      1. Set the **clientId** to the AppId of the bot identity.
      2. Set the **clientSecret** to the Secret that was created for your identity. *This is the `Secret Value` shown in the AppRegistration*.
      3. Set the **tenantId** to the Tenant Id where your application is registered.

1. Install the tool [dev tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows)   
1. Run `dev tunnels`. See [Create and host a dev tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows) and host the tunnel with anonymous user access command as shown below:

   ```bash
   devtunnel host -p 3978 --allow-anonymous
   ```

1. Take note of the url shown after `Connect via browser:`

4. On the Azure Bot, select **Settings**, then **Configuration**, and update the **Messaging endpoint** to `{tunnel-url}/api/messages`

5. Start the Agent using `npm start` (for JavaScript) or `python app.py` (for Python)

6. Select **Test in WebChat** on the Azure portal.


### Deploy to Azure

[TBD]


## Further reading

To learn more about building Bots and Agents, see our [Microsoft 365 Agents SDK](https://github.com/microsoft/agents) repo.