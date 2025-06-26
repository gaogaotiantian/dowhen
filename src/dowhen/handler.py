# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE


from __future__ import annotations

import sys
from types import FrameType
from typing import Any, Callable

from .callback import Callback
from .instrumenter import Instrumenter
from .trigger import Trigger

DISABLE = sys.monitoring.DISABLE


class EventHandler:
    def __init__(self, trigger: Trigger, callback: Callback):
        self.trigger = trigger
        self.callbacks: list[Callback] = [callback]
        self.disabled = False
        self.removed = False

    def disable(self) -> None:
        if self.removed:
            raise RuntimeError("Cannot disable a removed handler.")
        self.disabled = True

    def enable(self) -> None:
        if self.removed:
            raise RuntimeError("Cannot enable a removed handler.")
        if self.disabled:
            self.disabled = False
            Instrumenter().restart_events()

    def submit(self) -> None:
        Instrumenter().submit(self)

    def remove(self) -> None:
        Instrumenter().remove_handler(self)
        self.removed = True

    def __call__(self, frame: FrameType, **kwargs) -> Any:
        if not self.disabled:
            if not self.trigger.has_event(frame):
                return DISABLE
            should_fire = self.trigger.should_fire(frame)
            if should_fire is DISABLE:
                self.disable()
            elif should_fire:
                for cb in self.callbacks:
                    if cb(frame, **kwargs) is DISABLE:
                        self.disable()

        if self.disabled:
            return DISABLE

    def __enter__(self) -> "EventHandler":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.remove()

    def bp(self) -> "EventHandler":
        from .callback import Callback

        self.callbacks.append(Callback.bp())
        return self

    def do(self, func: str | Callable) -> "EventHandler":
        from .callback import Callback

        self.callbacks.append(Callback.do(func))
        return self

    def goto(self, target: str | int) -> "EventHandler":
        from .callback import Callback

        self.callbacks.append(Callback.goto(target))
        return self
