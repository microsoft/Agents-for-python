[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$RESOURCE_GROUP,

    [Parameter(Mandatory=$true)]
    [string]$BOT_NAME,

    [Parameter(Mandatory=$true)]
    [string]$ENDPOINT,

    [ValidateSet("secret", "fic")]
    [string]$AUTH_TYPE = 'secret',

    [string]$LOCATION = 'global',
    [string]$DEPLOYMENT_NAME = 'agent-deployment',

    [bool]$USE_TEAMS = $false
)


$appId = ./provision_app_registration.ps1 -g $RESOURCE_GROUP -n $BOT_NAME -e $ENDPOINT --auth_type $AUTH_TYPE -l $LOCATION -d $DEPLOYMENT_NAME --use_teams $USE_TEAMS

./provision_bot.ps1 -g $RESOURCE_GROUP -n $BOT_NAME -e $ENDPOINT --auth_type $AUTH_TYPE -l $LOCATION -d $DEPLOYMENT_NAME --app_id $appId

$appSecret = az ad app credential reset --id $appId --query password --output tsv

echo "App ID:"
echo $appId

echo "App Secret:"
echo $appSecret