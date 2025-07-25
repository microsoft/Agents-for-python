from microsoft.agents.activity import Attachment

class UserProfile:
    def __init__(self, transport: str = "", name: str = "", age: int = 0, picture: Attachment = None):
        self.transport = transport
        self.name = name
        self.age = age
        self.picture = picture
