from microsoft_agents.copilotstudio.client import CopilotClient, StartRequest
from microsoft_agents.activity import Activity, ActivityTypes


class ChatConsoleService:

    def __init__(self, copilot_client: CopilotClient, use_start_request: bool = False):
        self._copilot_client = copilot_client
        self._use_start_request = use_start_request

    async def start_service(self):
        print("agent> ")

        # Attempt to connect to the copilot studio hosted agent here
        # if successful, this will loop though all events that the Copilot Studio agent sends to the client setup the conversation.
        if self._use_start_request:
            # Use the new StartRequest model with optional locale
            start_request = StartRequest(
                emit_start_conversation_event=True,
                locale="en-US",  # Optional: specify locale
            )
            async for activity in self._copilot_client.start_conversation_with_request(
                start_request
            ):
                if not activity:
                    raise Exception(
                        "ChatConsoleService.start_service: Activity is None"
                    )
                self._print_activity(activity)
        else:
            # Use the simple start_conversation method
            async for activity in self._copilot_client.start_conversation():
                if not activity:
                    raise Exception(
                        "ChatConsoleService.start_service: Activity is None"
                    )
                self._print_activity(activity)

        # Once we are connected and have initiated the conversation,  begin the message loop with the Console.
        while True:
            question = input("user> ")

            # Send the user input to the Copilot Studio agent and await the response.
            # In this case we are not sending a conversation ID, as the agent is already connected by "StartConversationAsync", a conversation ID is persisted by the underlying client.
            async for activity in self._copilot_client.ask_question(question):
                self._print_activity(activity)

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
