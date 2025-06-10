# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import inspect

from .instrumenter import Instrumenter
from .util import call_in_frame, get_line_number


class Event:
    def __init__(self, code, event_type, event_data, condition=None):
        self.code = code
        self.event_type = event_type
        self.event_data = event_data
        self.condition = condition

    @classmethod
    def when(cls, entity, identifier, condition=None):
        if inspect.isfunction(entity):
            code = entity.__code__
        elif inspect.iscode(entity):
            code = entity
        else:
            raise TypeError(f"Unknown entity type: {type(entity)}")

        if isinstance(condition, str):
            try:
                compile(condition, "<string>", "eval")
            except SyntaxError as e:
                raise ValueError(f"Invalid condition expression: {condition}")
        elif condition is not None and not callable(condition):
            raise TypeError(
                f"Condition must be a string or callable, got {type(condition)}"
            )

        if identifier == "<start>":
            return cls(code, "start", {}, condition=condition)
        elif identifier == "<return>":
            return cls(code, "return", {}, condition=condition)

        line_number = get_line_number(code, identifier)
        if line_number is None:
            raise ValueError("Could not determine line number from identifier.")

        return cls(code, "line", {"line_number": line_number}, condition=condition)

    def do(self, func):
        from .callback import Callback

        return self._submit_callback(Callback(func))

    def goto(self, target):
        from .callback import Callback

        return self._submit_callback(Callback.goto(target))

    def should_fire(self, frame):
        if self.condition is None:
            return True
        try:
            if isinstance(self.condition, str):
                return eval(self.condition, frame.f_globals, frame.f_locals)
            elif callable(self.condition):
                return call_in_frame(self.condition, frame)
        except Exception as e:
            return False

        assert False, "Unknown condition type"  # pragma: no cover

    def _submit_callback(self, callback):
        from .event_handler import EventHandler

        handler = EventHandler(self, callback)
        Instrumenter().submit(handler)
        return handler


when = Event.when
