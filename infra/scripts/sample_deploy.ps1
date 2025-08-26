$RESOURCE_GROUP = 'robrandao-Resource'
$LOCATION = 'global'
$DEPLOYMENT_NAME = 'test-deployment'

az deployment group create -g $RESOURCE_GROUP -n $DEPLOYMENT_NAME --template-file ./main.bicep
    --parameter location=$LOCATION botName='robrandao-test-bot' addTeamsChannel=true oauthType='Aadv2WithFic' authType='ClientSecret'