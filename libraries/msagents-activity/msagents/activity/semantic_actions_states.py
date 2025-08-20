from enum import Enum


class SemanticActionsStates(str, Enum):
    start_action = "start"
    continue_action = "continue"
    done_action = "done"
