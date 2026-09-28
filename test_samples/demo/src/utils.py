from microsoft_teams.api.models import (
    MessagingExtensionAttachment,
    MessagingExtensionAttachmentLayout,
    MessagingExtensionResponse,
    MessagingExtensionResult,
    MessagingExtensionResultType,
)

def _thumbnail(title: str, text: str, tap_value: dict) -> dict:
    """Build a thumbnail-card preview whose tap fires a selectItem invoke.
    
    :param title: The title of the thumbnail card.
    :param text: The text content of the thumbnail card.
    :param tap_value: The value to include in the tap invoke action.
    :return: A dictionary representing the thumbnail card preview.
    """
    return {
        "title": title,
        "text": text,
        "tap": {"type": "invoke", "value": tap_value},
    }

def _list_result(
    *attachments: MessagingExtensionAttachment,
) -> MessagingExtensionResponse:
    """Wrap attachments in a list-layout composeExtension result.
    
    :param attachments: The messaging extension attachments to include in the list result.
    :return: A MessagingExtensionResponse containing the list of attachments.
    """
    return MessagingExtensionResponse(
        compose_extension=MessagingExtensionResult(
            type=MessagingExtensionResultType.RESULT,
            attachment_layout=MessagingExtensionAttachmentLayout.LIST,
            attachments=list(attachments),
        )
    )

def _adaptive_card(title: str, body_text: str) -> dict:
    """Build a minimal Adaptive Card with a bold title and a wrapped body line.
    
    :param title: The title of the adaptive card.
    :param body_text: The body text of the adaptive card.
    :return: A dictionary representing the adaptive card.
    """
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": title, "weight": "Bolder", "size": "Large"},
            {"type": "TextBlock", "text": body_text, "wrap": True, "isSubtle": True},
        ],
    }