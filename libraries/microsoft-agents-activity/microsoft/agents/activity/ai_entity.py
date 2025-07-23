# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum
from typing import List, Optional, Union, Literal
from dataclasses import dataclass

from .agents_model import AgentsModel
from .activity import Activity
from .entity import Entity


class ClientCitationIconName(str, Enum):
    """Enumeration of supported citation icon names."""

    MICROSOFT_WORD = "Microsoft Word"
    MICROSOFT_EXCEL = "Microsoft Excel"
    MICROSOFT_POWERPOINT = "Microsoft PowerPoint"
    MICROSOFT_ONENOTE = "Microsoft OneNote"
    MICROSOFT_SHAREPOINT = "Microsoft SharePoint"
    MICROSOFT_VISIO = "Microsoft Visio"
    MICROSOFT_LOOP = "Microsoft Loop"
    MICROSOFT_WHITEBOARD = "Microsoft Whiteboard"
    ADOBE_ILLUSTRATOR = "Adobe Illustrator"
    ADOBE_PHOTOSHOP = "Adobe Photoshop"
    ADOBE_INDESIGN = "Adobe InDesign"
    ADOBE_FLASH = "Adobe Flash"
    SKETCH = "Sketch"
    SOURCE_CODE = "Source Code"
    IMAGE = "Image"
    GIF = "GIF"
    VIDEO = "Video"
    SOUND = "Sound"
    ZIP = "ZIP"
    TEXT = "Text"
    PDF = "PDF"


class ClientCitationImage(AgentsModel):
    """Information about the citation's icon."""

    type: str = "ImageObject"
    name: str = ""


class SensitivityPattern(AgentsModel):
    """Pattern information for sensitivity usage info."""

    type: str = "DefinedTerm"
    in_defined_term_set: str = ""
    name: str = ""
    term_code: str = ""


class SensitivityUsageInfo(AgentsModel):
    """
    Sensitivity usage info for content sent to the user.
    This is used to provide information about the content to the user.
    """

    type: str = "https://schema.org/Message"
    schema_type: str = "CreativeWork"
    description: Optional[str] = None
    name: str = ""
    position: Optional[int] = None
    pattern: Optional[SensitivityPattern] = None


class ClientCitationAppearance(AgentsModel):
    """Appearance information for a client citation."""

    type: str = "DigitalDocument"
    name: str = ""
    text: Optional[str] = None
    url: Optional[str] = None
    abstract: str = ""
    encoding_format: Optional[str] = None
    image: Optional[ClientCitationImage] = None
    keywords: Optional[List[str]] = None
    usage_info: Optional[SensitivityUsageInfo] = None


class ClientCitation(AgentsModel):
    """
    Represents a Teams client citation to be included in a message.
    See Bot messages with AI-generated content for more details.
    https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/bot-messages-ai-generated-content?tabs=before%2Cbotmessage
    """

    type: str = "Claim"
    position: int = 0
    appearance: Optional[ClientCitationAppearance] = None

    def __post_init__(self):
        if self.appearance is None:
            self.appearance = ClientCitationAppearance()


class AIEntity(Entity):
    """Entity indicating AI-generated content."""

    type: str = "https://schema.org/Message"
    schema_type: str = "Message"
    context: str = "https://schema.org"
    id: str = ""
    additional_type: Optional[List[str]] = None
    citation: Optional[List[ClientCitation]] = None
    usage_info: Optional[SensitivityUsageInfo] = None

    def __post_init__(self):
        if self.additional_type is None:
            self.additional_type = ["AIGeneratedContent"]


def add_ai_to_activity(
    activity: Activity,
    citations: Optional[List[ClientCitation]] = None,
    usage_info: Optional[SensitivityUsageInfo] = None,
) -> None:
    """
    Adds AI entity to an activity to indicate AI-generated content.

    Args:
        activity: The activity to modify
        citations: Optional list of citations
        usage_info: Optional sensitivity usage information
    """
    if citations:
        ai_entity = AIEntity(
            type="https://schema.org/Message",
            schema_type="Message",
            context="https://schema.org",
            id="",
            additional_type=["AIGeneratedContent"],
            citation=citations,
            usage_info=usage_info,
        )

        if activity.entities is None:
            activity.entities = []

        activity.entities.append(ai_entity)
