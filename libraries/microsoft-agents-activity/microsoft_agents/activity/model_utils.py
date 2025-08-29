from .agents_model import AgentsModel

class ModelFieldHelper(ABC):
    def process(self, key: str) -> dict[str, Any]:
        raise NotImplemented()

class SkipIf(ModelFieldHelper, ABC):
    def __init__(self, value, check_condition: Callable[[Any], bool] = None):
        self.value = value
        if check_condition is None:
            self._skip = lambda v: v is None

    def process(self, key: str) -> dict[str, Any]:
        if self._skip(self.value):
            return {}
        return {key: self.value}

class SkipNone(SkipIf):
    def __init__(self, value):
        super().__init__(value)

def pick_model_dict(**kwargs):

    activity_dict = {}
    for key, value in kwargs.items():
        if not isinstance(value, ModelFieldHelper):
            activity_dict[key] = value
        else:
            activity_dict.update(value.process(key))

    return activity_dict

def pick_model(model_class: type[AgentsModel], **kwargs) -> AgentsModel:
    return model_class(**pick_model_dict(**kwargs))