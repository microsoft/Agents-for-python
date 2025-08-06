[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$RESOURCE_GROUP,

    [Parameter(Mandatory=$true)]
    [string]$BOT_NAME,

    [Parameter(Mandatory=$true)]
    [string]$ENDPOINT,

    [Parameter(Mandatory=$true)]
    [string]$APP_AUTH,

    [ValidateSet("secret", "fic")]
    [string]$AUTH_TYPE = 'secret',

    [string]$LOCATION = 'global',
    [string]$DEPLOYMENT_NAME = 'agent-deployment'

    [bool]$USE_TEAMS = $false
)

$appId = az deployment group create -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ./bicep/app_registration.bicep `
    --parameter endpoint=$ENDPOINT `
    --parameter botName=$BOT_NAME `
    --parameter useTeams=$USE_TEAMS `
    --query properties.outputs.appId.value --output tsv

az deployment group create -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ./bicep/bot.bicep `
    --parameter endpoint=$ENDPOINT `
    --parameter location=$LOCATION `
    --parameter botName=$BOT_NAME `
    --parameter appId=$appId
    
if ($USE_TEAMS) {
    az deployment group create -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ./bicep/teams_oauth.bicep `
        --parameter location=$LOCATION `
        --parameter botName=$BOT_NAME `
}

$appSecret = az ad app credential reset --id $appId --query password --output tsv

echo "App ID:"
echo $appId

echo "App Secret:"
echo $appSecret