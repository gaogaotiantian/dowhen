# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import sys

import pytest

import dowhen


def test_enable_disable():
    def f(x):
        return x

    handler = dowhen.do("x = 1").when(f, "return x")

    assert f(2) == 1
    handler.disable()
    assert f(2) == 2
    handler.enable()
    assert f(2) == 1
    handler.remove()
    assert f(2) == 2
    with pytest.raises(RuntimeError):
        handler.enable()


def test_event_handler_call():
    def f(x):
        return x

    x = 0  # This is the variable we will modify in the handler
    handler = dowhen.do("x = 1").when(f, "return x")
    frame = sys._getframe()
    handler(frame)
    assert x == 1

    x = 0
    handler.disable()
    handler(frame)
    assert x == 0


def test_remove():
    def f(x):
        return x

    def change(x):
        return {"x": 1}

    handler = dowhen.do(change).when(f, "return x")
    handler.remove()
    assert handler.removed is True

    assert f(0) == 0

    # double remove should be safe
    handler.remove()
