from microsoft.agents.activity import (
    ActionTypes,
    Activity,
    ActivityTypes,
    Attachment
)
from microsoft.agents.hosting.core import CardFactory, TurnContext

def button_obj(type: ActionTypes, value: str, title: str):
    return {
        "type": type,
        "value": value,
        "title": title
    }

class CardMessages:

    @staticmethod
    async def sendIntroCard (context: TurnContext):

        buttons = [
            button_obj(ActionTypes.im_back, "1", "Adaptive Card"),
            button_obj(ActionTypes.im_back, "2", "Animation Card"),
            button_obj(ActionTypes.im_back, "3", "Audio Card"),
            button_obj(ActionTypes.im_back, "4", "Hero Card"),
            button_obj(ActionTypes.im_back, "5", "Receipt Card"),
            button_obj(ActionTypes.im_back, "6", "Thumbnail Card"),
            button_obj(ActionTypes.im_back, "7", "Video Card")
        ]

        card = CardFactory.hero_card("", None, buttons, {"text": "Select one of the following choices"})
        await CardMessages.send_activity(context, card)

    @staticmethod
    async def send_adaptive_card(context: TurnContext, adaptive_card: dict):
        card = CardFactory.adaptive_card(adaptive_card)
        await CardMessages.send_activity(context, card)

    @staticmethod
    async def send_animation_card(context: TurnContext):
        card = CardFactory.animation_card(
            "Microsoft Agents Framework",
            [
                { "url": "https://i.giphy.com/Ki55RUbOV5njy.gif" }
            ],
            [],
            { "subtitle": "Animation Card" }
        )
        await CardMessages.send_activity(context, card)

    @staticmethod
    async def send_audio_card(context: TurnContext):
        card = CardFactory.audio_card(
            "I am your father",
            ["https://www.mediacollege.com/downloads/sound-effects/star-wars/darthvader/darthvader_yourfather.wav"],
            CardFactory.actions({
                "type": ActionTypes.open_url,
                "title": "Read more",
                "value": "https://en.wikipedia.org/wiki/The_Empire_Strikes_Back"
            }),
            {
                "subtitle": "Star Wars: Episode V - The Empire Strikes Back",
                "text": "The Empire Strikes Back (also known as Star Wars: Episode V – The Empire Strikes Back) is a 1980 American epic space opera film directed by Irvin Kershner. Leigh Brackett and Lawrence Kasdan wrote the screenplay, with George Lucas writing the film\'s story and serving as executive producer. The second installment in the original Star Wars trilogy, it was produced by Gary Kurtz for Lucasfilm Ltd. and stars Mark Hamill, Harrison Ford, Carrie Fisher, Billy Dee Williams, Anthony Daniels, David Prowse, Kenny Baker, Peter Mayhew and Frank Oz.",
                "image": { "url": "https://upload.wikimedia.org/wikipedia/en/3/3c/SW_-_Empire_Strikes_Back.jpg" }
            }
        )

        await CardMessages.send_activity(context, card)
        
    async def send_hero_card(context):
        card = CardFactory.hero_card(
            "Copilot Hero Card",
            CardFactory.images(['https://blogs.microsoft.com/wp-content/uploads/prod/2023/09/Press-Image_FINAL_16x9-4.jpg']),
            CardFactory.actions([
                {
                    "type": ActionTypes.open_url,
                    "title": "Get started",
                    "value": "https://docs.microsoft.com/en-us/azure/bot-service/"
                }
            ])
        )
        await CardMessages.send_activity(context, card)

    async def send_receipt_card(context):
        card = CardFactory.receipt_card({
            "title": "John Doe",
            "facts": [
                {
                    "key": "Order Number",
                    "value": "1234"
                },
                {
                    "key": "Payment Method",
                    "value": "VISA 5555-****"
                }
            ],
            "items": [
                {
                    "title": "Data Transfer",
                    "price": "$38.45",
                    "quantity": 368,
                    "image": { "url": "https://github.com/amido/azure-vector-icons/raw/master/renders/traffic-manager.png" }
                },
                {
                    "title": "App Service",
                    "price": "$45.00",
                    "quantity": 720,
                    "image": { "url": "https://github.com/amido/azure-vector-icons/raw/master/renders/cloud-service.png" }
                }
            ],
            "tax": "$7.50",
            "total": "$90.95",
            "buttons": CardFactory.actions([
                {
                    "type": ActionTypes.open_url,
                    "title": "More information",
                    "value": "https://azure.microsoft.com/en-us/pricing/details/bot-service/"
                }
            ])
        })
        await CardMessages.send_activity(context, card)

    @staticmethod
    async def send_thumbnail_card(context):
        card = CardFactory.thumbnail_card(
            "Copilot Thumbnail Card",
            CardFactory.images(['https://blogs.microsoft.com/wp-content/uploads/prod/2023/09/Press-Image_FINAL_16x9-4.jpg']),
            CardFactory.actions([
                {
                    "type": ActionTypes.open_url,
                    "title": "Get started",
                    "value": "https://docs.microsoft.com/en-us/azure/bot-service/"
                }
            ]),
            {
                "subtitle": "Your bots - wherever your users are talking",
                "text": "Build and connect intelligent bots to interact with your users naturally wherever they are, from text/sms to Skype, Slack, Office 365 mail and other popular services."
            }
        )
        await CardMessages.send_activity(context, card)
    
    @staticmethod
    async def send_video_card(context):
        card = CardFactory.video_card(
            "2018 Imagine Cup World Championship Intro",
            [{ "url": "https://sec.ch9.ms/ch9/783d/d57287a5-185f-4df9-aa08-fcab699a783d/IC18WorldChampionshipIntro2.mp4" }],
            [{
                "type": ActionTypes.OpenUrl,
                "title": "Lean More",
                "value": "https://channel9.msdn.com/Events/Imagine-Cup/World-Finals-2018/2018-Imagine-Cup-World-Championship-Intro"
            }],
            {
                "subtitle": "by Microsoft",
                "text": "Microsoft's Imagine Cup has empowered student developers around the world to create and innovate on the world stage for the past 16 years. These innovations will shape how we live, work and play."
            }
        )
        await CardMessages.send_activity(context, card)

    @staticmethod
    async def send_activity(context: TurnContext, card: Attachment):
        activity = Activity(
            type=ActivityTypes.Message,
            attachments=[card]
        )
        await context.send_activity(activity)