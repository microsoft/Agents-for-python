# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import copy
import random
import string
import json

from typing import Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from queue import Queue
from typing import Awaitable, Callable, List, Optional
from dataclasses import dataclass

from microsoft_agents.activity import Activity, ChannelAccount
from microsoft_agents.activity.activity import ConversationReference
from microsoft_agents.activity.activity_types import ActivityTypes
from microsoft_agents.activity.conversation_reference import ActivityEventNames
from microsoft_agents.hosting.core.middleware_set import Middleware, TurnContext
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class PagedResult(Generic[T]):
    items: List[T]
    continuation_token: Optional[str] = None


class TranscriptLogger(ABC):
    @abstractmethod
    async def log_activity(self, activity: Activity) -> None:
        """
        Asynchronously logs an activity.

        :param activity: The activity to log.
        """
        pass


class ConsoleTranscriptLogger(TranscriptLogger):
    """
    ConsoleTranscriptLogger writes activities to Console output. This is a DEBUG class, intended for testing
    and log tailing
    """

    async def log_activity(self, activity: Activity) -> None:
        """Log an activity to the transcript.
        :param activity:Activity being logged.
        """
        if not activity:
            raise TypeError("Activity is required")

        json_data = activity.model_dump_json()
        parsed = json.loads(json_data)
        print(json.dumps(parsed, indent=4))


class FileTranscriptLogger(TranscriptLogger):
    """
    A TranscriptLogger implementation that appends each activity as JSON to a file. This class appends
    each activity to the given file using basic formatting. This is a DEBUG class, intended for testing
    and log tailing.
    """

    def __init__(self, file_path: str, encoding: Optional[str] = "utf-8"):
        """
        Initializes the FileTranscriptLogger and opens the file for appending.

        :param file_path: Path to the transcript log file.
        :param encoding: File encoding (default: utf-8).
        """
        self.file_path = file_path
        self.encoding = encoding

        # Open file in append mode to ensure it exists
        self._file = open(self.file_path, "a", encoding=self.encoding)

    async def log_activity(self, activity: Activity) -> None:
        """
        Appends the given activity as a JSON line to the file. This method pretty-prints the JSON for readability, which makes
        it non-performant. For production scenarios, consider a more efficient logging mechanism.

        :param activity: The Activity object to log.
        """
        if not activity:
            raise TypeError("Activity is required")

        json_data = activity.model_dump_json()
        parsed = json.loads(json_data)

        self._file.write(json.dumps(parsed, indent=4))

        # As this is a logging / debugging class, we want to ensure the data is written out immediately. This is another
        # consideration that makes this class non-performant for production scenarios.
        self._file.flush()

    def __del__(self):
        if hasattr(self, "_file"):
            self._file.close()


class TranscriptLoggerMiddleware(Middleware):
    """Logs incoming and outgoing activities to a TranscriptLogger."""

    def __init__(self, logger: TranscriptLogger):
        if not logger:
            raise TypeError(
                "TranscriptLoggerMiddleware requires a TranscriptLogger instance."
            )

        self.logger = logger

    async def on_turn(
        self, context: TurnContext, logic: Callable[[TurnContext], Awaitable]
    ):
        """Initialization for middleware.
        :param context: Context for the current turn of conversation with the user.
        :param logic: Function to call at the end of the middleware chain.
        """
        transcript = Queue()
        activity = context.activity
        # Log incoming activity at beginning of turn
        if activity:
            if not activity.from_property:
                activity.from_property = ChannelAccount()
            if not activity.from_property.role:
                activity.from_property.role = "user"

            # We should not log ContinueConversation events used by skills to initialize the middleware.
            if not (
                context.activity.type == ActivityTypes.event
                and context.activity.name == ActivityEventNames.continue_conversation
            ):
                await self._queue_activity(transcript, copy.copy(activity))

        # hook up onSend pipeline
        # pylint: disable=unused-argument
        async def send_activities_handler(
            ctx: TurnContext,
            activities: List[Activity],
            next_send: Callable[[], Awaitable[None]],
        ):
            # Run full pipeline
            responses = await next_send()
            for index, activity in enumerate(activities):
                cloned_activity = copy.copy(activity)
                if responses and index < len(responses):
                    cloned_activity.id = responses[index].id

                # For certain channels, a ResourceResponse with an id is not always sent to the bot.
                # This fix uses the timestamp on the activity to populate its id for logging the transcript
                # If there is no outgoing timestamp, the current time for the bot is used for the activity.id
                if not cloned_activity.id:
                    alphanumeric = string.ascii_lowercase + string.digits
                    prefix = "g_" + "".join(
                        random.choice(alphanumeric) for i in range(5)
                    )
                    epoch = datetime.fromtimestamp(0, timezone.utc)
                    if cloned_activity.timestamp:
                        reference = cloned_activity.timestamp
                    else:
                        reference = datetime.now(timezone.utc)
                    delta = (reference - epoch).total_seconds() * 1000
                    cloned_activity.id = f"{prefix}{delta}"
                await self._queue_activity(transcript, cloned_activity)
            return responses

        context.on_send_activities(send_activities_handler)

        # hook up update activity pipeline
        async def update_activity_handler(
            ctx: TurnContext, activity: Activity, next_update: Callable[[], Awaitable]
        ):
            # Run full pipeline
            response = await next_update()
            update_activity = copy.copy(activity)
            update_activity.type = ActivityTypes.message_update
            await self._queue_activity(transcript, update_activity)
            return response

        context.on_update_activity(update_activity_handler)

        # hook up delete activity pipeline
        async def delete_activity_handler(
            ctx: TurnContext,
            reference: ConversationReference,
            next_delete: Callable[[], Awaitable],
        ):
            # Run full pipeline
            await next_delete()

            delete_msg = Activity(
                type=ActivityTypes.message_delete, id=reference.activity_id
            )
            deleted_activity: Activity = TurnContext.apply_conversation_reference(
                delete_msg, reference, False
            )
            await self._queue_activity(transcript, deleted_activity)

        context.on_delete_activity(delete_activity_handler)

        if logic:
            await logic()

        # Flush transcript at end of turn
        while not transcript.empty():
            activity = transcript.get()
            if activity is None:
                break
            await self.logger.log_activity(activity)
            transcript.task_done()

    async def _queue_activity(self, transcript: Queue, activity: Activity) -> None:
        """Logs the activity.
        :param transcript: transcript.
        :param activity: Activity to log.
        """
        transcript.put(activity)
