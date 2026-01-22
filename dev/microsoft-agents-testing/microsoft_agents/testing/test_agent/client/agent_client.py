class AgentClient:

    def submit_card_action(self, action):
        pass

    def send(self, message: str, delivery_mode: str = "default"):
        pass

    def send_activity(self, activity):
        pass

    def send_typing(self):
        pass

    def send_expect_replies(self, message: str, expected_replies: list[str]):
        pass

    def send_invoke(self, invoke):
        pass