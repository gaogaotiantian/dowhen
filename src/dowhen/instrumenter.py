# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt

from __future__ import annotations

import sys
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .event_handler import EventHandler


E = sys.monitoring.events


class Instrumenter:
    def __new__(self, *args, **kwargs):
        if not hasattr(self, "_instance"):
            self._instance = super().__new__(self)
            self._instance._intialized = False
        return self._instance

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
        event = event_handler.event
        if event.event_type == "line":
            self.register_line_event(
                event.code,
                event.event_data["line_number"],
                event_handler,
            )
        elif event.event_type == "start":
            self.register_start_event(event.code, event_handler)
        elif event.event_type == "return":
            self.register_return_event(event.code, event_handler)

    def register_line_event(self, code, line_number, event_handler: EventHandler):
        self.handlers[code].setdefault("line", {}).setdefault(line_number, []).append(
            event_handler
        )

        events = sys.monitoring.get_local_events(self.tool_id, code)
        sys.monitoring.set_local_events(self.tool_id, code, events | E.LINE)
        sys.monitoring.restart_events()

    def line_callback(self, code, line_number):  # pragma: no cover
        if code in self.handlers:
            for handler in self.handlers[code].get("line", {}).get(line_number, []):
                handler(sys._getframe(1))
        else:
            return sys.monitoring.DISABLE

    def register_start_event(self, code, event_handler: EventHandler):
        self.handlers[code].setdefault("start", []).append(event_handler)

        events = sys.monitoring.get_local_events(self.tool_id, code)
        sys.monitoring.set_local_events(self.tool_id, code, events | E.PY_START)
        sys.monitoring.restart_events()

    def start_callback(self, code, offset):  # pragma: no cover
        if code in self.handlers:
            for handler in self.handlers[code].get("start", []):
                handler(sys._getframe(1))
        else:
            return sys.monitoring.DISABLE

    def register_return_event(self, code, event_handler: EventHandler):
        self.handlers[code].setdefault("return", []).append(event_handler)

        events = sys.monitoring.get_local_events(self.tool_id, code)
        sys.monitoring.set_local_events(self.tool_id, code, events | E.PY_RETURN)
        sys.monitoring.restart_events()

    def return_callback(self, code, offset, retval):  # pragma: no cover
        if code in self.handlers:
            for handler in self.handlers[code].get("return", []):
                handler(sys._getframe(1))
        else:
            return sys.monitoring.DISABLE

    def remove_handler(self, event_handler: EventHandler):
        event = event_handler.event
        if (
            event.code not in self.handlers
            or event.event_type not in self.handlers[event.code]
        ):
            return
        if event.event_type == "line":
            handlers = self.handlers[event.code]["line"].get(
                event.event_data["line_number"], []
            )
        else:
            handlers = self.handlers[event.code][event.event_type]

        if event_handler in handlers:
            handlers.remove(event_handler)

            if event.event_type == "line" and not handlers:
                del self.handlers[event.code]["line"][event.event_data["line_number"]]

            if not self.handlers[event.code][event.event_type]:
                del self.handlers[event.code][event.event_type]
                events = sys.monitoring.get_local_events(self.tool_id, event.code)
                removed_event = {
                    "line": E.LINE,
                    "start": E.PY_START,
                    "return": E.PY_RETURN,
                }[event.event_type]

                sys.monitoring.set_local_events(
                    self.tool_id, event.code, events & ~removed_event
                )


def clear_all():
    Instrumenter().clear_all()
