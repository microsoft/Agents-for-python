# OBO Auth Sample

This Agent has been created using [Microsoft 365 Agents SDK](https://github.com/microsoft/agents-for-net), it shows how to use authorization in your Agent using OAuth and OBO.

- The sample uses the Agent SDK User Authorization capabilities in [Azure Bot Service](https://docs.botframework.com), providing features to make it easier to develop an Agent that authorizes users with various identity providers such as Azure AD (Azure Active Directory), GitHub, Uber, etc.
- This sample shows how to use an OBO Exchange to update the default token with a custom scope on behalf of the user.

## Prerequisites

- [Python](https://www.python.org/) version 3.9 or higher
- [dev tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows) (for local development)

## Local Setup

### Configuration

1. [Create an Azure Bot](https://aka.ms/AgentsSDK-CreateBot)
   - Record the Application ID, the Tenant ID, and the Client Secret for use below

1. Configuring the token connection in the Agent settings
    1. Open the `env.TEMPLATE` file in the root of the sample project, rename it to `.env` and configure the following values:
      1. Set the **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID** to the AppId of the bot identity.
      2. Set the **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET** to the Secret that was created for your identity. *This is the `Secret Value` shown in the AppRegistration*.
      3. Set the **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID** to the Tenant Id where your application is registered.
  
1. [Add OAuth to your bot](https://aka.ms/AgentsSDK-AddAuth) using the _Azure Active Directory v2_ Provider.

1. Configure the authorization handlers
   1. Open the `.env` file and add the name of the OAuth Connections, note the prefix must match the name of the auth handlers in the code, so for:

    ```python
    @AGENT_APP.message("obo", auth_handlers=["GRAPH"])
    ```

    you should have one pair of environmental variables for `GRAPH`:

    ```env
    AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=
    AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__OBOCONNECTIONNAME=
    ```

    In this sample, this is the only auth handler.
      

1. Run `dev tunnels`. See [Create and host a dev tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows) and host the tunnel with anonymous user access command as shown below:

   ```bash
   devtunnel host -p 3978 --allow-anonymous
   ```

1. Take note of the url shown after `Connect via browser:`

1. On the Azure Bot, select **Settings**, then **Configuration**, and update the **Messaging endpoint** to `{tunnel-url}/api/messages`

### Running the Agent

1. Open this folder from your IDE or Terminal of preference
1. (Optional but recommended) Set up virtual environment and activate it.
1. Install dependencies

```sh
pip install -r requirements.txt
```

### Run in localhost, anonymous mode

1. Start the application

```sh
python -m src.main
```

At this point you should see the message 

```text
======== Running on http://localhost:3978 ========
```

The agent is ready to accept messages.

## Accessing the Agent

### Using the Agent in WebChat

1. Go to your Azure Bot Service resource in the Azure Portal and select **Test in WebChat**

## Further reading

To learn more about building Bots and Agents, see our [Microsoft 365 Agents SDK](https://github.com/microsoft/agents) repo.