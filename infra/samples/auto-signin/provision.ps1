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

    [ValidateSet('secret', 'fic')]
    [string]$AUTH_TYPE,

    
    [ValidateSet('aadv2', 'none')]
    [string]$OAUTH_TYPE = 'aadv2',

    [Alias('l')]
    [string]$LOCATION = 'global',

    [Alias('d')]
    [string]$DEPLOYMENT_NAME = 'agent-deployment',

    [string]$USE_TEAMS = 'false'
)

$appId = ./provision_app.ps1 -g $RESOURCE_GROUP -n $BOT_NAME -e $ENDPOINT -d $DEPLOYMENT_NAME -USE_TEAMS $USE_TEAMS

./provision_bot.ps1 -g $RESOURCE_GROUP -n $BOT_NAME -e $ENDPOINT -AUTH_TYPE $AUTH_TYPE -l $LOCATION -d $DEPLOYMENT_NAME -APP_ID $appId -OAUTH_TYPE $OAUTH_TYPE

$appSecret = az ad app credential reset --id $appId --query password --output tsv

echo "App ID:"
echo $appId

echo "App Secret:"
echo $appSecret