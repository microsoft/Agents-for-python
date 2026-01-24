# Copilot Studio Agent Connector Sample

This sample demonstrates how to create an agent that can receive requests from Microsoft Copilot Studio via Power Apps Connector and use OAuth/OBO (On-Behalf-Of) token exchange to access Microsoft Graph on behalf of the user.

## Overview

This sample shows:
- Handling connector requests from Microsoft Copilot Studio (RoleTypes.connector_user)
- Using ConnectorUserAuthorization for OBO token exchange
- Calling Microsoft Graph API with the exchanged token
- Responding to Copilot Studio with personalized messages

## Prerequisites

1. Azure Bot resource with App Registration
2. Microsoft Copilot Studio agent configured to use the connector
3. OAuth Connection configured for Graph API access
4. Python 3.10 or higher

## Configuration

### 1. App Registration Setup

Create or use an existing App Registration in Azure:
- Note the Application (client) ID
- Note the Directory (tenant) ID
- Create a client secret

### 2. Configure appsettings.json

```json
{
  "TokenValidation": {
    "Enabled": true,
    "Audiences": [
      "{{ClientId}}"
    ],
    "TenantId": "{{TenantId}}"
  },
  "Connections": {
    "ServiceConnection": {
      "Settings": {
        "AuthType": "ClientSecret",
        "AuthorityEndpoint": "https://login.microsoftonline.com/{{TenantId}}",
        "ClientId": "{{ClientId}}",
        "ClientSecret": "{{ClientSecret}}"
      }
    },
    "GraphConnection": {
      "Settings": {
        "AuthType": "ClientSecret",
        "AuthorityEndpoint": "https://login.microsoftonline.com/{{TenantId}}",
        "ClientId": "{{ClientId}}",
        "ClientSecret": "{{ClientSecret}}",
        "Scopes": ["https://graph.microsoft.com/.default"]
      }
    }
  },
  "AgentApplication": {
    "UserAuthorization": {
      "Handlers": {
        "connector": {
          "Type": "ConnectorUserAuthorization",
          "Settings": {
            "Name": "connector",
            "OBOConnectionName": "GraphConnection",
            "Scopes": ["https://graph.microsoft.com/.default"]
          }
        }
      }
    }
  }
}
```

Replace:
- `{{ClientId}}` - Your App Registration client ID
- `{{TenantId}}` - Your Azure AD tenant ID  
- `{{ClientSecret}}` - Your App Registration client secret

### 3. Copilot Studio Configuration

In Microsoft Copilot Studio:
1. Create or edit your agent
2. Add a Power Apps Connector action
3. Configure the connector to point to your agent's endpoint
4. Enable authentication with your App Registration

## Running the Sample

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the agent:
```bash
python app.py
```

3. For local development, use a tunneling tool (ngrok, devtunnels):
```bash
devtunnels create
devtunnels host -p 3978 --allow-anonymous
```

4. Update your Azure Bot messaging endpoint with the tunnel URL

## Code Structure

### app.py
Main application entry point that:
- Configures the agent with authentication
- Sets up user authorization with ConnectorUserAuthorization
- Registers the custom agent

### agent.py
The MyAgent class that:
- Checks for connector_user role messages
- Retrieves the OBO-exchanged token
- Calls Microsoft Graph to get user information
- Sends a personalized greeting

## Key Concepts

### Connector User Authorization

The ConnectorUserAuthorization handler:
1. Extracts the security token from the incoming request
2. Checks token expiration
3. Performs OBO token exchange to get a Graph API token
4. Returns the exchanged token for API calls

### Message Flow

1. Copilot Studio sends message to agent with recipient.role = "connectoruser"
2. Agent receives message and detects connector_user role
3. Agent calls `UserAuthorization.GetTurnTokenAsync()` to get the exchanged Graph token
4. Agent uses token to call Microsoft Graph
5. Agent sends response back to Copilot Studio

## Security Notes

- Never store secrets in source code or appsettings.json in production
- Use Azure Key Vault or environment variables for sensitive values
- Ensure proper token validation is enabled
- Use secure communication (HTTPS) in production

## Troubleshooting

### Token Exchange Fails
- Verify OBO connection is configured correctly
- Check that scopes match your API permissions
- Ensure App Registration has proper permissions granted

### Authentication Errors
- Verify client ID and tenant ID are correct
- Check that client secret is valid and not expired
- Ensure TokenValidation settings match your App Registration

### Connector Not Receiving Messages
- Verify Azure Bot messaging endpoint is correct
- Check that Copilot Studio connector is configured properly
- Ensure authentication is set up in both places

## Related Documentation

- [Microsoft Agents SDK for Python](https://github.com/microsoft/Agents-for-python)
- [Microsoft Copilot Studio](https://learn.microsoft.com/microsoft-copilot-studio/)
- [On-Behalf-Of OAuth Flow](https://learn.microsoft.com/entra/identity-platform/v2-oauth2-on-behalf-of-flow)
