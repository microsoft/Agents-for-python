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

    [ValidateSet("secret")]
    [string]$AUTH_TYPE = 'secret',

    [string]$LOCATION = 'global',
    [string]$DEPLOYMENT_NAME = 'agent-deployment'

    [Parameter(Mandatory=$true)]
    [string]$APP_ID
)

az deployment group what-if -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ./bicep/bot.bicep `
    --parameter endpoint=$ENDPOINT `
    --parameter location=$LOCATION `
    --parameter botName=$BOT_NAME `
    --parameter appId=$appId