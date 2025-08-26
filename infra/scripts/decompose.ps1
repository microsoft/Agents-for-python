# References for ARM and Graph resource types
# https://learn.microsoft.com/en-us/azure/templates/microsoft.botservice/botservices?pivots=deployment-language-bicep
# https://learn.microsoft.com/en-us/graph/templates/bicep/reference/applications?view=graph-bicep-1.0

$CHANNEL_NAME_LIST = @('msteams', 'webchat', 'directline', 'email')
$RESOURCE_GROUP = 'robrandao-resource'
$BOT_NAME = 'robrandao-another'

# Azure Bot Service Channels
echo 'Showing configured channels'
foreach($channel_name in $CHANNEL_NAME_LIST) {
    echo 'Channel: $channel_name'
    az bot $CHANNEL_NAME show -n $BOT_NAME -g $RESOURCE_GROUP
    echo '\n'
}

# Azure Bot Service Connections
echo 'Showing connections'
az bot authsetting list -n $BOT_NAME -g $RESOURCE_GROUP
echo '\n'

# do more...