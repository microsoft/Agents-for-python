$ENDPOINT = 'https://nxlf1rdl-3978.usw2.devtunnels.ms/api/messages'
$LOCATION = 'global'
$RESOURCE_GROUP = 'robrandao-resource'
$DEPLOYMENT_NAME = 'test-deployment'
$BOT_NAME = 'robrandao-dev-bot-test'
$OAUTH_CONNECTION_NAME = 'oauth-secret'

az deployment group create -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ./main.bicep `
    --parameter endpoint=$ENDPOINT `
    --parameter location=$LOCATION `
    --parameter botName=$BOT_NAME `
    --parameter addTeamsChannel=true `
    --parameter oauthType='Aadv2' `
    --parameter authType='ClientSecret' `
    --parameter oauthConnectionName=$OAUTH_CONNECTION_NAME `
