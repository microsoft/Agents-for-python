from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class SemanticAction(AgentsModel):
    """Represents a reference to a programmatic action.

    :param id: ID of this action
    :type id: str
    :param entities: Entities associated with this action
    :type entities: dict[str, :class:`microsoft_agents.activity.entity.Entity`]
    :param state: State of this action. Allowed values: `start`, `continue`, `done`
    :type state: str or :class:`microsoft_agents.activity.semantic_action_states.SemanticActionStates`
    """

    id: NonEmptyString
    entities: dict = None
    state: NonEmptyString = None
