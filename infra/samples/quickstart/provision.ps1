[CmdletBinding()]
param(
    # [Parameter(Mandatory=$true)]
    [Alias('g')]
    [string]$RESOURCE_GROUP='robrandao-resource',

    # [Parameter(Mandatory=$true)]
    [Alias('n')]
    [string]$BOT_NAME='rob-p-quickstart',

    # [Parameter(Mandatory=$true)]
    [Alias('e')]
    [string]$ENDPOINT='https://nxlf1rdl-3978.usw2.devtunnels.ms/api/messages',

    [ValidateSet('clientsecret')]
    [string]$AUTH_TYPE = 'clientsecret',

    [Alias('l')]
    [string]$LOCATION = 'global',

    [Alias('d')]
    [string]$DEPLOYMENT_NAME = 'agent-deployment'
)

$appId = az deployment group create -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ../../bicep/simple_app_registration.bicep `
    --parameter botName=$BOT_NAME `
    --query properties.outputs.appId.value --output tsv

az deployment group create -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ../../bicep/bot.bicep `
    --parameter appId=$appId `
    --parameter endpoint=$ENDPOINT `
    --parameter location=$LOCATION `
    --parameter botName=$BOT_NAME `
    --query properties.outputs.appId.value --output tsv

$appSecret = az ad app credential reset --id $appId --query password --output tsv

Write-Output "App ID:"
Write-Output $appId

Write-Output "App Secret:"
Write-Output $appSecret