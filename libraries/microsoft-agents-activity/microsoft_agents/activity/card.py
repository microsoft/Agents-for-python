# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod

from .activity import Activity
from .agents_model import AgentsModel
from .attachment import Attachment
from .activity_types import ActivityTypes


class Card(AgentsModel, ABC):
    """Base class for rich cards that can be sent to a user as an Attachment.

    Each concrete card implements :meth:`to_attachment` to wrap itself in an attachment using its
    own content type. :meth:`to_message` builds on that to produce a ready-to-send message activity.
    """

    @abstractmethod
    def to_attachment(self) -> Attachment:
        """
        Creates a new Attachment that wraps this card.

        :returns: The generated attachment.
        """
        raise NotImplementedError(
            "to_attachment must be implemented by concrete Card subclasses."
        )

    def to_message(self) -> Activity:
        """
        Creates a new message activity that includes this card as an attachment.

        :returns: An Activity representing a message activity with the card attached.
        """
        return Activity(type=ActivityTypes.message, attachments=[self.to_attachment()])
