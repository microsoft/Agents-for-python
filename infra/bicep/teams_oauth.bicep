param botName string
param location string

resource azureBot 'microsoft.botService/botServices@2023-09-15-preview' existing ={
  name: botName
}

resource msteams 'microsoft.botService/botServices/channels@2023-09-15-preview' = {
  parent: azureBot
  location: location
  name: 'MsTeamsChannel'
  properties: {
    channelName: 'MsTeamsChannel'
  }
}
