# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


from __future__ import annotations

from types import FrameType

from .callback import Callback
from .trigger import Trigger


class EventHandler:
    def __init__(self, trigger: Trigger, callback: Callback):
        self.trigger = trigger
        self.callback = callback
        self.enabled = True
        self.removed = False

    def disable(self) -> None:
        self.enabled = False

    def enable(self) -> None:
        if self.removed:
            raise RuntimeError("Cannot enable a removed handler.")
        self.enabled = True

    def remove(self) -> None:
        from .instrumenter import Instrumenter

        Instrumenter().remove_handler(self)
        self.removed = True

    def __call__(self, frame: FrameType) -> None:
        if self.enabled and self.trigger.should_fire(frame):
            self.callback(frame)
