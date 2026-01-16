from dataclasses import dataclass

@dataclass
class CheckInfo:
    value: Any # current value being checked
    path: list[str | int] # path to the value within the data structure
    root: Any # root object
    parent: Any | None # parent value