@description('The name of the Azure Bot resource.')
param botName string

@description('The ID for an existing App Registration')
param appId string

@description('The endpoint for the bot service.')
param endpoint string

@description('The location for the bot service.')
param location string

@allowed([
  'aadv2'
  'none'
])
@description('The OAuth method to use for connections.')
param oauthType string


resource azureBot 'microsoft.botService/botServices@2023-09-15-preview' = {
  name: botName
  location: location
  kind: 'azurebot'
  properties: {
    displayName: botName
    msaAppId: appId
    endpoint: endpoint
    msaAppType: 'SingleTenant'
    msaAppTenantId: tenant().tenantId
    // schemaTransformationVersion: '1.3'
  }
}

// for now, automatically add Graph connection if oauthType is aadv2
resource graphConnectionSettings 'microsoft.botService/botServices/connections@2023-09-15-preview' = if (oauthType == 'aadv2') {
  parent: azureBot
  location: location
  name: 'graph-oauth'
  properties: {
    name: 'graph-oauth'
    serviceProviderDisplayName: 'Azure Active Directory v2'
    serviceProviderId: '30dd229c-58e3-4a48-bdfd-91ec48eb906c'
    clientId: appId
    clientSecret: '' // needs to be manually set
    scopes: 'User.Read openId profile'
    parameters: [
      {
        key: 'tenantId'
        value: tenant().tenantId
      }
    ]
  }
}
