from ast import In
from typing import Optional
from microsoft_agents.activity import Attachment
from microsoft_agents.hosting.corei port (
    ConnectorClient,
    InputFile,
    InputFileDownloader,
    TurnContext,
    TurnState
)

class TeamsAttachmentDownloader(InputFileDownloader):

    def __init__(self, state_key: str = "inputFiles"):
        self._http_client = None
        self._state_key = state_key

    async def download_files(context: TurnContext) -> list[InputFile]:
        attachments = context.activity.attachments
        if attachments:
            attachments = [
                a for a in context.activity.attachments if a.content_type.startswith("text/html")
            ]

        if not attachments:
            return []

        connector_client = context.turn_state.get("connectorClient") # robrandao: TODO
        self._http_client.defaults.headers = connector_client.http_client.defaults.headers

        files = []
        for attachment in attachments:
            file = await self.download_file(attachment)
            if file:
                files.append(file)

        return files
    
    async def download_file(self, attachment: Attachment) -> Optional[InputFile]:
        input_file = None
        # robrandao: TODO
        if attachment.content_type == "application/vnd.microsoft.teams.file.download.info":
            pass

    async def download_and_store_files(self, context: TurnContext, state: TState) -> None:
        files = await self.download_files(context)
        state.set_value(self._state_key, files)
