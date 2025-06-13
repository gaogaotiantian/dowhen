# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import io
import sys
import textwrap

import pytest

import dowhen


def test_do_when():
    def f(x):
        return x

    dowhen.do("x = 1").when(f, "return x")
    assert f(2) == 1
    dowhen.clear_all()
    assert f(2) == 2


def test_do_when_with_function():
    def f(x, y):
        return x + y

    def change(x, y):
        x = 2
        y = 3
        return {"x": x, "y": y}

    dowhen.do(change).when(f, "return x + y")
    assert f(1, 1) == 5


def test_do_when_with_method():
    def f(x):
        return x

    class A:
        def change(self, x):
            return {"x": 1}

    dowhen.do(A().change).when(f, "return x")


def test_callback_call():
    x = 0
    callback = dowhen.do("x = 1")
    frame = sys._getframe()
    callback(frame)
    assert x == 1


def test_callback_writeback():
    x = 0

    def change(x):
        return {"x": 1}

    def change_with_frame(_frame):
        return {"x": _frame.f_locals["x"] + 1}

    def change_wrong(x):
        return {"y": 1}

    def change_wrong_tyoe(x):
        return [1]

    frame = sys._getframe()
    callback = dowhen.do(change)
    callback(frame)
    assert x == 1

    callback = dowhen.do(change_with_frame)
    callback(frame)
    assert x == 2

    with pytest.raises(TypeError):
        callback_wrong = dowhen.do(change_wrong)
        callback_wrong(frame)

    with pytest.raises(TypeError):
        callback_wrong_type = dowhen.do(change_wrong_tyoe)
        callback_wrong_type(frame)

    callback = dowhen.do(change)
    del x
    with pytest.raises(TypeError):
        callback(frame)

    dowhen.clear_all()


def test_callback_invalid_type():
    with pytest.raises(TypeError):
        dowhen.do(123)

    def f(x):
        return x

    def change(y):
        return {"y": 1}

    def change_wrong(x):
        return {"y": 1}

    def change_wrong_tyoe(x):
        return [1]

    with pytest.raises(TypeError):
        dowhen.do(change).when(f, "return x")
        f(0)

    with pytest.raises(TypeError):
        dowhen.do(change_wrong).when(f, "return x")
        f(0)

    with pytest.raises(TypeError):
        dowhen.do(change_wrong_tyoe).when(f, "return x")
        f(0)


def test_frame():
    def f(x):
        return x

    def cb(_frame):
        return {"x": _frame.f_locals["x"] + 1}

    dowhen.do(cb).when(f, "return x")
    assert f(0) == 1


def test_goto():
    def f():
        x = 0
        assert False
        x = 1
        return x

    dowhen.goto("x = 1").when(f, "assert False")
    assert f() == 1


def test_bp():
    def f(x):
        x = x + 1
        return x

    command = textwrap.dedent("""
        w
        n
        c
    """)

    command_input = io.StringIO(command)
    command_input2 = io.StringIO(command)

    output = io.StringIO()
    output2 = io.StringIO()

    _stdin = sys.stdin
    _stdout = sys.stdout
    _trace_func = sys.gettrace()
    try:
        sys.stdin = command_input
        sys.stdout = output
        dowhen.bp().when(f, "x = x + 1")
        # coverage confuses pdb
        sys.settrace(None)
        f(0)
        sys.settrace(_trace_func)

        sys.stdin = command_input2
        sys.stdout = output2
        dowhen.when(f, "return x").bp()
        sys.settrace(None)
        f(0)
        sys.settrace(_trace_func)
    finally:
        sys.settrace(_trace_func)
        sys.stdin = _stdin
        sys.stdout = _stdout

    for out in (output.getvalue(), output2.getvalue()):
        assert "x = x + 1" in out
        assert "(Pdb)" in out
        assert "test_bp()" in out
        assert "return x" in out
