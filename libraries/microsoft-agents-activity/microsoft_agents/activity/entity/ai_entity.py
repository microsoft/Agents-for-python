# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from enum import Enum
from typing import List, Optional, Literal

from ..agents_model import AgentsModel
from ._schema_mixin import _SchemaMixin
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


class SensitivityPattern(AgentsModel, _SchemaMixin):
    """Pattern information for sensitivity usage info."""

    at_type: Literal["DefinedTerm"] = "DefinedTerm"

    in_defined_term_set: str = ""
    name: str = ""
    term_code: str = ""


class SensitivityUsageInfo(AgentsModel, _SchemaMixin):
    """
    Sensitivity usage info for content sent to the user.
    This is used to provide information about the content to the user.
    """

    type: str = "https://schema.org/Message"
    at_type: Literal["CreativeWork"] = "CreativeWork"

    description: Optional[str] = None
    name: str = ""
    position: Optional[int] = None
    pattern: Optional[SensitivityPattern] = None

    def __init__(self, **data):  # removes linter errors for user-facing code
        super().__init__(**data)


class ClientCitationAppearance(AgentsModel, _SchemaMixin):
    """Appearance information for a client citation."""

    at_type: Literal["DigitalDocument"] = "DigitalDocument"

    name: str = ""
    text: Optional[str] = None
    url: Optional[str] = None
    abstract: str = ""
    encoding_format: Optional[str] = None
    image: Optional[ClientCitationImage] = None
    keywords: Optional[List[str]] = None
    usage_info: Optional[SensitivityUsageInfo] = None

    def __init__(self, **data):  # removes linter errors for user-facing code
        super().__init__(**data)


class ClientCitation(AgentsModel, _SchemaMixin):
    """
    Represents a Teams client citation to be included in a message.
    See Bot messages with AI-generated content for more details.
    https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/bot-messages-ai-generated-content?tabs=before%2Cbotmessage
    """

    at_type: Literal["Claim"] = "Claim"

    position: int = 0
    appearance: Optional[ClientCitationAppearance] = None

    def __init__(self, **data):  # removes linter errors for user-facing code
        super().__init__(**data)

    def __post_init__(self):
        if self.appearance is None:
            self.appearance = ClientCitationAppearance()


class AIEntity(Entity, _SchemaMixin):
    """Entity indicating AI-generated content."""

    at_type: Literal["Message"] = "Message"
    at_context: Literal["https://schema.org"] = "https://schema.org"

    type: str = "https://schema.org/Message"
    id: str = ""
    additional_type: Optional[List[str]] = None
    citation: Optional[List[ClientCitation]] = None
    usage_info: Optional[SensitivityUsageInfo] = None

    def __init__(self, **data):  # removes linter errors for user-facing code
        super().__init__(**data)

    def __post_init__(self):
        if self.additional_type is None:
            self.additional_type = ["AIGeneratedContent"]
