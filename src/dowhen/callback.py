# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import ctypes
import inspect
import sys
import warnings

from .instrumenter import Instrumenter
from .util import call_in_frame, get_line_number


class Callback:
    def __init__(self, func, **kwargs):
        if isinstance(func, str):
            pass
        elif inspect.isfunction(func):
            self.func_args = inspect.getfullargspec(func).args
        elif inspect.ismethod(func):
            self.func_args = inspect.getfullargspec(func).args
        else:
            raise TypeError(f"Unsupported callback type: {type(func)}. ")
        self.func = func
        self.kwargs = kwargs

    def __call__(self, frame):
        if isinstance(self.func, str):
            if self.func == "goto":  # pragma: no cover
                self.call_goto(frame)
            else:
                self.call_code(frame)
        elif inspect.isfunction(self.func) or inspect.ismethod(self.func):
            self.call_function(frame)
        else:  # pragma: no cover
            assert False, "Unknown callback type"

        if sys.version_info < (3, 13):
            LocalsToFast = ctypes.pythonapi.PyFrame_LocalsToFast
            LocalsToFast.argtypes = [ctypes.py_object, ctypes.c_int]
            LocalsToFast(frame, 0)

    def call_code(self, frame):
        exec(self.func, frame.f_globals, frame.f_locals)

    def call_function(self, frame):
        writeback = call_in_frame(self.func, frame)

        f_locals = frame.f_locals
        if isinstance(writeback, dict):
            for arg, val in writeback.items():
                if arg not in f_locals:
                    raise TypeError(f"Argument '{arg}' not found in frame locals.")
                f_locals[arg] = val
        elif writeback is not None:
            raise TypeError(
                "Callback function must return a dictionary for writeback, or None, "
                f"got {type(writeback)} instead."
            )

    def call_goto(self, frame):  # pragma: no cover
        # Changing frame.f_lineno is only allowed in trace functions so it's
        # impossible to get coverage for this function
        target = self.kwargs["target"]
        line_number = get_line_number(frame.f_code, target)
        if line_number is None:
            raise ValueError(f"Could not determine line number for target: {target}")
        with warnings.catch_warnings():
            # This gives a RuntimeWarning in Python 3.12
            warnings.simplefilter("ignore", RuntimeWarning)
            frame.f_lineno = line_number

    @classmethod
    def do(cls, func):
        return cls(func)

    @classmethod
    def goto(cls, target):
        return cls("goto", target=target)

    def when(self, entity, identifier):
        from .event import when

        event = when(entity, identifier)
        from .event_handler import EventHandler

        handler = EventHandler(event, self)
        Instrumenter().submit(handler)

        return handler


do = Callback.do
goto = Callback.goto
