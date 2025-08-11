param botName string = 'rob-july-3-test'
param endpoint string = 'https://nxlf1rdl-3978.usw2.devtunnels.ms/api/messages'
param location string = 'global'
param oauthType string = 'None'
param useTeams bool = true

module appRegistration 'app_registration.bicep' = {
  name: 'appRegistration'
  params: {
    botName: botName
    useTeams: useTeams
    endpoint: endpoint
  }
}

module azureBot 'bot.bicep' = {
  name: 'azureBot'
  params: {
    botName: botName
    endpoint: endpoint
    appId: appRegistration.outputs.appId
    location: location
    oauthType: oauthType
  }
}

output appId string = appRegistration.outputs.appId
