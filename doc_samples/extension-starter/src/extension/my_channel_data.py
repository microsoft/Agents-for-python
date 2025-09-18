from typing import Optional

from microsoft_agents.activity import AgentsModel

class MyChannelData(AgentsModel):
    
    user_id: Optional[str] = None
    custom_field: Optional[str] = None

def get_my_channel_data(context):

    data = MyChannelData(
        user_id=context.activity.from_property.id,
        custom_field=context.activity.channel_data.get("custom_field")
    )

    return data