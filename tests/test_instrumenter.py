# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import dis
import sys

import dowhen
from dowhen.instrumenter import Instrumenter

from .util import disable_coverage

E = sys.monitoring.events


def test_local_events():
    def f(x):
        return x

    handler_line = dowhen.do("x = 1").when(f, "return x")
    assert sys.monitoring.get_local_events(Instrumenter().tool_id, f.__code__) == E.LINE

    dowhen.do("x = 1").when(f, "<start>")
    assert (
        sys.monitoring.get_local_events(Instrumenter().tool_id, f.__code__)
        == E.LINE | E.PY_START
    )

    dowhen.do("x = 1").when(f, "<return>")
    assert (
        sys.monitoring.get_local_events(Instrumenter().tool_id, f.__code__)
        == E.LINE | E.PY_START | E.PY_RETURN
    )

    handler_line.remove()
    assert (
        sys.monitoring.get_local_events(Instrumenter().tool_id, f.__code__)
        == E.PY_START | E.PY_RETURN
    )

    dowhen.clear_all()
    assert (
        sys.monitoring.get_local_events(Instrumenter().tool_id, f.__code__)
        == E.NO_EVENTS
    )


def test_events_on_same_line():
    def f(x):
        return x

    handler1 = dowhen.do("x = 1").when(f, "return x")
    handler2 = dowhen.do("x = 1").when(f, "return x")

    assert sys.monitoring.get_local_events(Instrumenter().tool_id, f.__code__) == E.LINE

    handler1.remove()
    assert sys.monitoring.get_local_events(Instrumenter().tool_id, f.__code__) == E.LINE

    handler2.remove()
    assert (
        sys.monitoring.get_local_events(Instrumenter().tool_id, f.__code__)
        == E.NO_EVENTS
    )


def test_line_event_disabled():
    def f(x):
        x += 1
        return x

    dowhen.do("x = 1").when(f, "return x")
    with disable_coverage():
        f(0)
    assert (
        len(
            [
                inst
                for inst in dis.get_instructions(f, adaptive=True)
                if inst.opname == "INSTRUMENTED_LINE"
            ]
        )
        == 1
    )
