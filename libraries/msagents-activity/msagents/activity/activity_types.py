from enum import Enum


class ActivityTypes(str, Enum):
    message = "message"
    contact_relation_update = "contactRelationUpdate"
    conversation_update = "conversationUpdate"
    typing = "typing"
    end_of_conversation = "endOfConversation"
    event = "event"
    invoke = "invoke"
    invoke_response = "invokeResponse"
    delete_user_data = "deleteUserData"
    message_update = "messageUpdate"
    message_delete = "messageDelete"
    installation_update = "installationUpdate"
    message_reaction = "messageReaction"
    suggestion = "suggestion"
    trace = "trace"
    handoff = "handoff"
    command = "command"
    command_result = "commandResult"
