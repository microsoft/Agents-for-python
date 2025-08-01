# OBO Auth

This Agent has been created using [Microsoft 365 Agents SDK](https://github.com/microsoft/agents-for-net), it shows how to use authorization in your Agent using OAuth and OBO.

- The sample uses the Agent SDK User Authorization capabilities in [Azure Bot Service](https://docs.botframework.com), providing features to make it easier to develop an Agent that authorizes users with various identity providers such as Azure AD (Azure Active Directory), GitHub, Uber, etc.
- This sample shows how to use an OBO Exchange to update the default token with a custom scope on behalf of the user.

## Prerequisites

- [Python](https://www.python.org/) version 3.9 or higher
- [dev tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows) (for local development)

## Configuration and Execution

1. [Create an Azure Bot](https://aka.ms/AgentsSDK-CreateBot)
   - Record the Application ID, the Tenant ID, and the Client Secret for use below

1. Configuring the token connection in the Agent settings
   > The instructions for this sample are for a SingleTenant Azure Bot using ClientSecrets.  The token connection configuration will vary if a different type of Azure Bot was configured.  For more information see [TODO](contoso.com)

  1. Open the `env.TEMPLATE` file in the root of the sample project and rename it to `.env`
  1. Update **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID**, **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID** and **CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET**
  

1. Configure the authorization handlers
   1. Open the `.env` file and add the name of the OAuth Connections, note the prefix must match the name of the auth handlers in the code, so for:

    ```python
    @AGENT_APP.message("obo", auth_handlers=["GRAPH"])
    ```

    you should have one item for `graph` and aonther for `github`

    ```env
    AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__AZUREBOTOAUTHCONNECTIONNAME=
    AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__GRAPH__SETTINGS__OBOCONNECTIONNAME=
    ```

    In this sample, this is the only auth handler to worry about.
      

1. Run `dev tunnels`. Please follow [Create and host a dev tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows) and host the tunnel with anonymous user access command as shown below:

   ```bash
   devtunnel host -p 3978 --allow-anonymous
   ```

1. Update your Azure Bot ``Messaging endpoint`` with the tunnel Url:  `{tunnel-url}/api/messages`

1. Run the bot from a terminal with `python -m src.main`

1. Test via "Test in WebChat"" on your Azure Bot in the Azure Portal.

## Interacting with the Agent

TODO