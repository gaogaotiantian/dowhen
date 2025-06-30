# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE

from __future__ import annotations

import sys
from collections import defaultdict
from types import CodeType, FrameType
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .handler import EventHandler

E = sys.monitoring.events
DISABLE = sys.monitoring.DISABLE


class Instrumenter:
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> Instrumenter:
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, tool_id: int = 4):
        if not self._initialized:
            self.tool_id = tool_id
            self.handlers: defaultdict[CodeType | None, dict] = defaultdict(dict)

            sys.monitoring.use_tool_id(self.tool_id, "dowhen instrumenter")
            sys.monitoring.register_callback(self.tool_id, E.LINE, self.line_callback)
            sys.monitoring.register_callback(
                self.tool_id, E.PY_RETURN, self.return_callback
            )
            sys.monitoring.register_callback(
                self.tool_id, E.PY_START, self.start_callback
            )
            self._initialized = True

    def clear_all(self) -> None:
        for code in self.handlers:
            if code is None:
                sys.monitoring.set_events(self.tool_id, E.NO_EVENTS)
            else:
                sys.monitoring.set_local_events(self.tool_id, code, E.NO_EVENTS)
        self.handlers.clear()

    def submit(self, event_handler: "EventHandler") -> None:
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

    def register_line_event(
        self, code: CodeType | None, line_number: int, event_handler: "EventHandler"
    ) -> None:
        self.handlers[code].setdefault("line", {}).setdefault(line_number, []).append(
            event_handler
        )

        if code is None:
            events = sys.monitoring.get_events(self.tool_id)
            sys.monitoring.set_events(self.tool_id, events | E.LINE)
        else:
            events = sys.monitoring.get_local_events(self.tool_id, code)
            sys.monitoring.set_local_events(self.tool_id, code, events | E.LINE)
        sys.monitoring.restart_events()

    def line_callback(self, code: CodeType, line_number: int):  # pragma: no cover
        handlers = []
        if None in self.handlers:
            handlers.extend(self.handlers[None].get("line", {}).get(line_number, []))
            handlers.extend(self.handlers[None].get("line", {}).get(None, []))
        if code in self.handlers:
            handlers.extend(self.handlers[code].get("line", {}).get(line_number, []))
            handlers.extend(self.handlers[code].get("line", {}).get(None, []))
        if handlers:
            return self._process_handlers(handlers, sys._getframe(1))
        return sys.monitoring.DISABLE

    def register_start_event(
        self, code: CodeType | None, event_handler: "EventHandler"
    ) -> None:
        self.handlers[code].setdefault("start", []).append(event_handler)

        if code is None:
            events = sys.monitoring.get_events(self.tool_id)
            sys.monitoring.set_events(self.tool_id, events | E.PY_START)
        else:
            events = sys.monitoring.get_local_events(self.tool_id, code)
            sys.monitoring.set_local_events(self.tool_id, code, events | E.PY_START)
        sys.monitoring.restart_events()

    def start_callback(self, code: CodeType, offset: int):  # pragma: no cover
        handlers = []
        if None in self.handlers:
            handlers.extend(self.handlers[None].get("start", []))
        if code in self.handlers:
            handlers.extend(self.handlers[code].get("start", []))
        if handlers:
            return self._process_handlers(handlers, sys._getframe(1))
        return sys.monitoring.DISABLE

    def register_return_event(
        self, code: CodeType | None, event_handler: "EventHandler"
    ) -> None:
        self.handlers[code].setdefault("return", []).append(event_handler)

        if code is None:
            events = sys.monitoring.get_events(self.tool_id)
            sys.monitoring.set_events(self.tool_id, events | E.PY_RETURN)
        else:
            events = sys.monitoring.get_local_events(self.tool_id, code)
            sys.monitoring.set_local_events(self.tool_id, code, events | E.PY_RETURN)
        sys.monitoring.restart_events()

    def return_callback(
        self, code: CodeType, offset: int, retval: object
    ):  # pragma: no cover
        handlers = []
        if None in self.handlers:
            handlers.extend(self.handlers[None].get("return", []))
        if code in self.handlers:
            handlers.extend(self.handlers[code].get("return", []))
        if handlers:
            return self._process_handlers(handlers, sys._getframe(1), retval=retval)
        return sys.monitoring.DISABLE

    def _process_handlers(
        self, handlers: list["EventHandler"], frame: FrameType, **kwargs
    ):  # pragma: no cover
        disable = sys.monitoring.DISABLE
        for handler in handlers:
            disable = handler(frame, **kwargs) and disable
        return sys.monitoring.DISABLE if disable else None

    def restart_events(self) -> None:
        sys.monitoring.restart_events()

    def remove_handler(self, event_handler: "EventHandler") -> None:
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
                    removed_event = {
                        "line": E.LINE,
                        "start": E.PY_START,
                        "return": E.PY_RETURN,
                    }[event.event_type]

                    if code is None:
                        events = sys.monitoring.get_events(self.tool_id)
                        sys.monitoring.set_events(self.tool_id, events & ~removed_event)
                    else:
                        events = sys.monitoring.get_local_events(self.tool_id, code)
                        sys.monitoring.set_local_events(
                            self.tool_id, code, events & ~removed_event
                        )


def clear_all() -> None:
    Instrumenter().clear_all()
