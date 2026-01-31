from .core import ActivityTemplate

class ActivityBuilder:
    def __init__(self, template: dict | ActivityTemplate | None = None):

        if isinstance(template, dict):
            self._template = ActivityTemplate(template)
        elif isinstance(template, ActivityTemplate):
            self._template = template
        else:
            self._template = ActivityTemplate()
        
    def build(self) -> ActivityTemplate:
        pass

    def build_template(self) -> ActivityTemplate

    def start_conversation(self) -> Activity:
        ...

    def end_conversation(self) -> Activity:
        ...