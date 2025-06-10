# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import inspect

from .instrumenter import Instrumenter
from .util import get_line_number


class Event:
    def __init__(self, code, event_type, event_data):
        self.code = code
        self.event_type = event_type
        self.event_data = event_data

    @classmethod
    def when(cls, entity, identifier):
        if inspect.isfunction(entity):
            code = entity.__code__
        elif inspect.iscode(entity):
            code = entity
        else:
            raise TypeError(f"Unknown entity type: {type(entity)}")

        if identifier == "<start>":
            return cls(code, "start", {})
        elif identifier == "<return>":
            return cls(code, "return", {})

        line_number = get_line_number(code, identifier)
        if line_number is None:
            raise ValueError("Could not determine line number from identifier.")

        return cls(code, "line", {"line_number": line_number})

    def do(self, func):
        from .callback import Callback

        return self._submit_callback(Callback(func))

    def goto(self, target):
        from .callback import Callback

        return self._submit_callback(Callback.goto(target))

    def _submit_callback(self, callback):
        from .event_handler import EventHandler

        handler = EventHandler(self, callback)
        Instrumenter().submit(handler)
        return handler


when = Event.when
