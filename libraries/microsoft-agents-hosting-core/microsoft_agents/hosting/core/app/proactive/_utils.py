# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
    
from microsoft_agents.hosting.core.telemetry.core import BaseSpanWrapper
from .conversation import Conversation

def _link_to_conversation(conversation: Conversation, span: BaseSpanWrapper) -> None:
    """Links the given span to the conversation reference of the given conversation, if it exists.
    This allows telemetry related to the span to be correlated with telemetry related to the conversation reference,
    enabling better observability and debugging of proactive scenarios.
    
    :param conversation: The conversation whose conversation reference should be linked to the span
    :type conversation: Conversation
    :param span: The span to link to the conversation reference
    :type span: BaseSpanWrapper
    """
    if conversation.conversation_reference is not None:
        
         span.otel_span.add_link(conversation.conversation_reference.to_span_link())