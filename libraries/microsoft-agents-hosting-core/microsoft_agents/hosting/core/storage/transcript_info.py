from datetime import datetime, timezone, timedelta

class TranscriptInfo:
    def __init__(self):
        self.ChannelId : str = ""
        self.ConversationId : str = ""
        self.CreatedOn : datetime = datetime.min        
