from microsoft.agents.botbuilder import ActivityHandler, MessageFactory, TurnContext
from microsoft.agents.core.models import ChannelAccount, Activity, EndOfConversationCodes


class Bot2(ActivityHandler):
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hi, This is Bot2")

    async def on_message_activity(self, turn_context: TurnContext):
        if any(stop_message in turn_context.activity.text for stop_message in ["stop", "end"]):
            await turn_context.send_activity("(Bot2) Ending conversation from Bot2")
            end_of_conversation = Activity.create_end_of_conversation_activity()
            end_of_conversation.code = EndOfConversationCodes.completed_successfully
            await turn_context.send_activity(end_of_conversation)
        else:
            await turn_context.send_activity(f"Echo(Bot2): {turn_context.activity.text}")
            await turn_context.send_activity("Echo(Bot2): Say \"end\" or \"stop\" and I'll end the conversation and return to the parent.")
    
    async def on_end_of_conversation_activity(self, turn_context):
        return
