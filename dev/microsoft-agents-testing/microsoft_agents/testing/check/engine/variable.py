from fn import _ as underscore

def variable(name: str):
    return underscore.get(name)

_actual = variable("actual")
_root = variable("root")
_parent = variable("parent")
_ = _actual