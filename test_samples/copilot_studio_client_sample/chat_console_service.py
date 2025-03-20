from microsoft.agents.copilotstudio.client import CopilotClient
from microsoft.agents.core.models import Activity, ActivityTypes


class ChatConsoleService:

    def __init__(self, copilot_client: CopilotClient):
        self._copilot_client = copilot_client

    async def start_service(self):
        print("bot> ")

        # Attempt to connect to the copilot studio hosted bot here
        # if successful, this will loop though all events that the Copilot Studio bot sends to the client setup the conversation.
        async for activity in self._copilot_client.start_conversation():
            if not activity:
                raise Exception("ChatConsoleService.start_service: Activity is None")

            self._print_activity(activity)

        # Once we are connected and have initiated the conversation,  begin the message loop with the Console.
        while True:
            question = input("user> ")

            # Send the user input to the Copilot Studio bot and await the response.
            # In this case we are not sending a conversation ID, as the agent is already connected by "StartConversationAsync", a conversation ID is persisted by the underlying client.
            async for bot_activity in self._copilot_client.ask_question(question):
                self._print_activity(bot_activity)

    @staticmethod
    def _print_activity(activity: Activity):
        if activity.type == ActivityTypes.message:
            if activity.text_format == "markdown":
                print(activity.text)
                if activity.suggested_actions and activity.suggested_actions.actions:
                    print("Suggested actions:")
                    for action in activity.suggested_actions.actions:
                        print(f"  - {action.text}")
            else:
                print(activity.text)
        elif activity.type == ActivityTypes.typing:
            print(".")
        elif activity.type == ActivityTypes.event:
            print("+")
        else:
            print(f"Activity type: [{activity.type}]")
