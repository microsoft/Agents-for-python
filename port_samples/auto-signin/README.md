# AutoSignIn

This Agent has been created using [Microsoft 365 Agents SDK](https://github.com/microsoft/agents-for-python), it shows how to use Auto SignIn user authorization in your Agent.

This sample uses different routes, and some are configured to use one or more auth handlers. Below is an abbreviate version of the decorators used to configure the routes, which are really commands to the Agent:

```python
  @AGENT_APP.message("/status")
  @AGENT_APP.message("/logout")
  @AGENT_APP.message("/me", auth_handlers=["GRAPH"])
  @AGENT_APP.message("/prs", auth_handlers=["GITHUB"])
```


The sample uses the bot OAuth capabilities in [Azure Bot Service](https://docs.botframework.com), providing features to make it easier to develop a bot that authorizes users to various identity providers such as Azure AD (Azure Active Directory), GitHub, Uber, etc.

- ## Prerequisites

-  [Python](https://www.python.org/) version 3.9 or higher
-  [dev tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows) (for local development)

## Configure Azure Bot Service

1. [Create an Azure Bot](https://aka.ms/AgentsSDK-CreateBot)
   - Record the Application ID, the Tenant ID, and the Client Secret for use below

1. [Add OAuth to your bot](https://aka.ms/AgentsSDK-AddAuth) using the _Azure Active Directory v2_ Provider.

1. Create a second Azure Bot **OAuth Connection** using the _GitHub_ provider.

  > To configure OAuth for GitHub you need a GitHub account, under settings/developer settings/OAuth apps, create a new OAuth app, and set the callback URL to `https://token.botframework.com/.auth/web/redirect`. Then you will need to provide the clientId and clientSecret, and the required scopes: `user repo`

1. Configuring the token connection in the Agent settings
   > The instructions for this sample are for a SingleTenant Azure Bot using ClientSecrets.  The token connection configuration will vary if a different type of Azure Bot was configured.  For more information see [TODO](contoso.com)

  1. Open the `env.TEMPLATE` file in the root of the sample project and rename it to `.env`
  1. Update **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID**, **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID** and **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET**
  

1. Configure the UserAuthorization handlers
   1. Open the `.env` file and add the name of the OAuth Connections, note the prefix must match the name of the auth handlers in the code, so for:

    ```python
        @AGENT_APP.message("/me", auth_handlers=["GRAPH"])
        @AGENT_APP.message("/prs", auth_handlers=["GITHUB"])
    ```

    you should have one item for `GRAPH` and aonther for `GITHUB`

    ```env
        AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=
        AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__OBOCONNECTIONNAME=m
        AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GITHUB__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=
        AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GITHUB__SETTINGS__OBOCONNECTIONNAME=
    ```
      

1. Run `dev tunnels`. Please follow [Create and host a dev tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows) and host the tunnel with anonymous user access command as shown below:

   ```bash
   devtunnel host -p 3978 --allow-anonymous
   ```

1. Update your Azure Bot ``Messaging endpoint`` with the tunnel Url:  `{tunnel-url}/api/messages`

1. Run the bot from a terminal with `python -m src.main` after installing all of the dependencies (see the empty-agent sample).

1. Test via "Test in WebChat"" on your Azure Bot in the Azure Portal.

TODO, running in teams

## Interacting with the Agent

- When the conversation starts, you will be greeted with a welcome message, and another message informing the token status. 
- Sending `/me` will trigger the OAuth flow and display additional information about you.
- Note that if running this in Teams and SSO is setup, you shouldn't see any "sign in" prompts.  This is true in this sample since we are only requesting a basic set of scopes that Teams doesn't require additional consent for.

## Further reading
To learn more about building Agents, see our [Microsoft 365 Agents SDK](https://github.com/microsoft/agents) repo.
