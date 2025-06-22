# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


from __future__ import annotations

import sys
from types import FrameType
from typing import Any

from .callback import Callback
from .trigger import Trigger

DISABLE = sys.monitoring.DISABLE


class EventHandler:
    def __init__(self, trigger: Trigger, callback: Callback):
        self.trigger = trigger
        self.callback = callback
        self.enabled = True
        self.removed = False

    def disable(self) -> None:
        if self.removed:
            raise RuntimeError("Cannot disable a removed handler.")
        self.enabled = False

    def enable(self) -> None:
        if self.removed:
            raise RuntimeError("Cannot enable a removed handler.")
        if not self.enabled:
            self.enabled = True
            from .instrumenter import Instrumenter

            Instrumenter().restart_events()

    def remove(self) -> None:
        from .instrumenter import Instrumenter

        Instrumenter().remove_handler(self)
        self.removed = True

    def __call__(self, frame: FrameType) -> Any:
        if self.enabled:
            should_fire = self.trigger.should_fire(frame)
            if should_fire is DISABLE:
                self.disable()
            elif should_fire:
                if self.callback(frame) is DISABLE:
                    self.disable()

        if not self.enabled:
            return DISABLE
