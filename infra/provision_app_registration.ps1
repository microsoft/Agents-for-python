[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [Alias('g')]
    [string]$RESOURCE_GROUP,

    [Parameter(Mandatory=$true)]
    [Alias('n')]
    [string]$BOT_NAME,

    [Parameter(Mandatory=$true)]
    [Alias('e')]
    [string]$ENDPOINT,

    [Alias('d')]
    [string]$DEPLOYMENT_NAME = 'agent-deployment',

    [string]$USE_TEAMS = 'false'
)

$appId = az deployment group create -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ./bicep/app_registration.bicep `
    --parameter endpoint=$ENDPOINT `
    --parameter botName=$BOT_NAME `
    --parameter useTeams=$USE_TEAMS `
    --query properties.outputs.appId.value --output tsv

Write-Output $appId