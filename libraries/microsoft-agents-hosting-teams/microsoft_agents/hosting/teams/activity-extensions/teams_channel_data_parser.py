from .teams_channel_data import TeamsChannelData

def parse_teams_channel_data(data: dict) -> TeamsChannelData:
    return TeamsChannelData.model_validate(data)