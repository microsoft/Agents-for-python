from microsoft_agents.hosting.core import ActivityHandler, TurnContext
from microsoft_agents.activity import (
    ChannelAccount,
    Activity,
    EndOfConversationCodes,
)


class Agent2(ActivityHandler):
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hi, This is Agent2")

    async def on_message_activity(self, turn_context: TurnContext):
        if any(
            stop_message in turn_context.activity.text
            for stop_message in ["stop", "end"]
        ):
            await turn_context.send_activity("(Agent2) Ending conversation from Agent2")
            end_of_conversation = Activity.create_end_of_conversation_activity()
            end_of_conversation.code = EndOfConversationCodes.completed_successfully
            await turn_context.send_activity(end_of_conversation)
        else:
            await turn_context.send_activity(
                f"Echo(Agent2): {turn_context.activity.text}"
            )
            await turn_context.send_activity(
                'Echo(Agent2): Say "end" or "stop" and I\'ll end the conversation and return to the parent.'
            )

    async def on_end_of_conversation_activity(self, turn_context):
        return
