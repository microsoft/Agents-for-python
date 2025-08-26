$ENDPOINT = 'https://nxlf1rdl-3978.usw2.devtunnels.ms/api/messages'
$LOCATION = 'global'
$RESOURCE_GROUP = 'robrandao-resource'
$DEPLOYMENT_NAME = 'test-deployment-fic'
$BOT_NAME = 'robrandao-fic-test-alt'
$OAUTH_CONNECTION_NAME = 'robrandao-oauth-fic'

$appId = az deployment group create -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ./main.bicep `
    --parameter endpoint=$ENDPOINT `
    --parameter location=$LOCATION `
    --parameter botName=$BOT_NAME `
    --parameter addTeamsChannel=true `
    --parameter oauthType='Aadv2WithFic' `
    --parameter authType='ClientSecret' `
    --parameter oauthConnectionName=$OAUTH_CONNECTION_NAME `
    --query properties.outputs.appId.value --output tsv

$appSecret = az ad app credential reset --id $appId --query password --output tsv

echo "App ID:"
echo $appId

echo "App Secret:"
echo $appSecret