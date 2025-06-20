# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt

from __future__ import annotations

import sys
from collections import defaultdict

from .handler import EventHandler

E = sys.monitoring.events


class Instrumenter:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
            cls._instance._intialized = False
        return cls._instance

    def __init__(self, tool_id=4):
        if not self._intialized:
            self.tool_id = tool_id
            self.handlers = defaultdict(dict)

            sys.monitoring.use_tool_id(self.tool_id, "dowhen instrumenter")
            sys.monitoring.register_callback(self.tool_id, E.LINE, self.line_callback)
            sys.monitoring.register_callback(
                self.tool_id, E.PY_RETURN, self.return_callback
            )
            sys.monitoring.register_callback(
                self.tool_id, E.PY_START, self.start_callback
            )
            self._intialized = True

    def clear_all(self):
        for code in self.handlers:
            sys.monitoring.set_local_events(self.tool_id, code, E.NO_EVENTS)
        self.handlers.clear()

    def submit(self, event_handler: EventHandler):
        trigger = event_handler.trigger
        for event in trigger.events:
            code = event.code
            if event.event_type == "line":
                assert (
                    isinstance(event.event_data, dict)
                    and "line_number" in event.event_data
                )
                self.register_line_event(
                    code,
                    event.event_data["line_number"],
                    event_handler,
                )
            elif event.event_type == "start":
                self.register_start_event(code, event_handler)
            elif event.event_type == "return":
                self.register_return_event(code, event_handler)

    def register_line_event(self, code, line_number, event_handler: EventHandler):
        self.handlers[code].setdefault("line", {}).setdefault(line_number, []).append(
            event_handler
        )

        events = sys.monitoring.get_local_events(self.tool_id, code)
        sys.monitoring.set_local_events(self.tool_id, code, events | E.LINE)
        sys.monitoring.restart_events()

    def line_callback(self, code, line_number):  # pragma: no cover
        if code in self.handlers:
            handlers = self.handlers[code].get("line", {}).get(line_number, [])
            handlers.extend(self.handlers[code].get("line", {}).get(None, []))
            if handlers:
                for handler in handlers:
                    handler(sys._getframe(1))
                return
        return sys.monitoring.DISABLE

    def register_start_event(self, code, event_handler: EventHandler):
        self.handlers[code].setdefault("start", []).append(event_handler)

        events = sys.monitoring.get_local_events(self.tool_id, code)
        sys.monitoring.set_local_events(self.tool_id, code, events | E.PY_START)
        sys.monitoring.restart_events()

    def start_callback(self, code, offset):  # pragma: no cover
        if code in self.handlers:
            handlers = self.handlers[code].get("start", [])
            if handlers:
                for handler in handlers:
                    handler(sys._getframe(1))
                return
        return sys.monitoring.DISABLE

    def register_return_event(self, code, event_handler: EventHandler):
        self.handlers[code].setdefault("return", []).append(event_handler)

        events = sys.monitoring.get_local_events(self.tool_id, code)
        sys.monitoring.set_local_events(self.tool_id, code, events | E.PY_RETURN)
        sys.monitoring.restart_events()

    def return_callback(self, code, offset, retval):  # pragma: no cover
        if code in self.handlers:
            handlers = self.handlers[code].get("return", [])
            if handlers:
                for handler in handlers:
                    handler(sys._getframe(1))
                return
        return sys.monitoring.DISABLE

    def remove_handler(self, event_handler: EventHandler):
        trigger = event_handler.trigger
        for event in trigger.events:
            code = event.code
            if code not in self.handlers or event.event_type not in self.handlers[code]:
                continue
            if event.event_type == "line":
                assert (
                    isinstance(event.event_data, dict)
                    and "line_number" in event.event_data
                )
                handlers = self.handlers[code]["line"].get(
                    event.event_data["line_number"], []
                )
            else:
                handlers = self.handlers[code][event.event_type]

            if event_handler in handlers:
                handlers.remove(event_handler)

                if event.event_type == "line" and not handlers:
                    assert (
                        isinstance(event.event_data, dict)
                        and "line_number" in event.event_data
                    )
                    del self.handlers[code]["line"][event.event_data["line_number"]]

                if not self.handlers[code][event.event_type]:
                    del self.handlers[code][event.event_type]
                    events = sys.monitoring.get_local_events(self.tool_id, code)
                    removed_event = {
                        "line": E.LINE,
                        "start": E.PY_START,
                        "return": E.PY_RETURN,
                    }[event.event_type]

                    sys.monitoring.set_local_events(
                        self.tool_id, code, events & ~removed_event
                    )


def clear_all():
    Instrumenter().clear_all()
