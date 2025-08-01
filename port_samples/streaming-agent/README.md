# Streaming Agent Sample

This is a sample of a simple Agent that is hosted on a Python web service.  This Agent is demonstrate the streaming OpenAI streamed responses.

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

1. Configure **AZURE_OPENAI_API_VERSION** and **AZURE_OPENAI_ENDPOINT** in `.env` to point to the API version and endpoint set up in Azure AI Foundry

1. Run `dev tunnels`. Please follow [Create and host a dev tunnel](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started?tabs=windows) and host the tunnel with anonymous user access command as shown below:

   ```bash
   devtunnel host -p 3978 --allow-anonymous
   ```

1. Update your Azure Bot ``Messaging endpoint`` with the tunnel Url:  `{tunnel-url}/api/messages`

1. Run the bot from a terminal with `python -m src.main` after installing all of the dependencies (see the empty-agent sample).

1. Test via "Test in WebChat"" on your Azure Bot in the Azure Portal.

## Interacting with the Agent

- When the conversation starts (you may have to reset the chat), you will be greeted with a welcome message. Enter `poem` to initiate the streamed response.