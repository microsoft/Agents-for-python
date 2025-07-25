import json

from microsoft.agents.activity import (
    Activity,
    ActivityTypes
)
from microsoft.agents.hosting.core import (
    ActivityHandler
)
from .card_messages import CardMessages

AdaptiveCard = json.load(open("./resources/adaptive_card.json", "r"))

# robrandao: import adaptive card (see JS repo)

class CardSampleAgent(ActivityHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    async def on_members_added(self, context, next):
        members_added = context.activity.members_added
        for i, member in enumerate(members_added):
            if (context.activity.recipient is not None and
                members_added[i] != context.activity.recipient.id):

                await CardMessages.send_intro_card(context)
                await next()

    async def on_message(self, context, activity):
        if context.activity.text is not None:
            pre = context.activity.text.lower()[0].lower()

            if pre == "1":
                await CardMessages.send_adaptive_card(context, AdaptiveCard)
            else:

                funcs = {
                    "display card options": CardMessages.send_intro_card,
                    "2": CardMessages.send_animation_card,
                    "3": CardMessages.send_audio_card,
                    "4": CardMessages.send_hero_card,
                    "5": CardMessages.send_receipt_card,
                    "6": CardMessages.send_thumbnail_card,
                    "7": CardMessages.send_video_card
                }
                
                if pre in funcs:
                    await funcs[pre](context)
                elif pre == "1":
                    await CardMessages.send_adaptive_card(context, AdaptiveCard)
                else:
                    reply = Activity.from_object({
                        "type": ActivityTypes.Message,
                        "text": "Your input was not recognized, please try again."
                    })
                    await context.send_activity(reply)
                    await CardMessages.send_intro_card(context)
        else:
            await context.send_activity("This sample is only for testing Cards using CardFatory methods." \
                "Please refer to other samples to test out more functionalities")
        await next()