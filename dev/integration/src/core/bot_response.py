class BotResponse:
    
    def __init__(self):
        pass

    def handle_streamed_activity(self, activity: Activity, sact: StreamInfo, cid: str) -> bool:
        pass

    def dispose_async(self) -> ValueTask:
        pass

    @property
    def service_endpoint(self) -> str:
        pass