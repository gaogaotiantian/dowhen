# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE


import sys

import pytest

import dowhen

from .util import do_pdb_test


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

        @classmethod
        def classmethod_change(cls, x):
            return {"x": 2}

        @staticmethod
        def staticmethod_change(x):
            return {"x": 3}

    with dowhen.do(A().change).when(f, "return x"):
        assert f(2) == 1

    with dowhen.do(A.classmethod_change).when(f, "return x"):
        assert f(3) == 2

    with dowhen.do(A.staticmethod_change).when(f, "return x"):
        assert f(4) == 3


def test_callback_call():
    x = 0
    callback = dowhen.do("x = 1")
    frame = sys._getframe()
    callback(frame)
    assert x == 1


def test_method_callback_call():
    class A:
        def change(self, x):
            return {"x": 1}

    x = 0
    callback = dowhen.do(A().change)
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

    def change_wrong_type(x):
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
        callback_wrong_type = dowhen.do(change_wrong_type)
        callback_wrong_type(frame)

    callback = dowhen.do(change)
    del x
    with pytest.raises(TypeError):
        callback(frame)

    dowhen.clear_all()


def test_callback_retval():
    def f(x):
        return x

    retval_holder = []

    def cb(_retval):
        retval_holder.append(_retval)

    with dowhen.do(cb).when(f, "<return>"):
        assert f(0) == 0
        assert retval_holder == [0]

    with pytest.raises(TypeError):
        with dowhen.do(cb).when(f, "return x"):
            f(0)

    retval_holder.clear()
    callback = dowhen.do(cb)
    frame = sys._getframe()
    assert callback(frame, retval=0) is None
    assert retval_holder == [0]

    with pytest.raises(TypeError):
        callback(frame)


def test_callback_disable():
    def cb():
        return dowhen.DISABLE

    callback = dowhen.do(cb)
    frame = sys._getframe()
    assert callback(frame) is dowhen.DISABLE


def test_callback_invalid_type():
    with pytest.raises(TypeError):
        dowhen.do(123)

    def f(x):
        return x

    def change(y):
        return {"y": 1}

    def change_wrong(x):
        return {"y": 1}

    def change_wrong_type(x):
        return [1]

    with pytest.raises(TypeError):
        dowhen.do(change).when(f, "return x")
        f(0)

    with pytest.raises(TypeError):
        dowhen.do(change_wrong).when(f, "return x")
        f(0)

    with pytest.raises(TypeError):
        dowhen.do(change_wrong_type).when(f, "return x")
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
        if x == 0:
            assert False
        x = 1
        return x

    with dowhen.goto("x = 1").when(f, "assert False"):
        assert f() == 1

    with dowhen.goto("+1").when(f, "assert False"):
        assert f() == 1


def test_bp():
    def f(x):
        x = x + 1
        return x

    command = """
        w
        n
        c
    """

    handler1 = dowhen.bp().when(f, "x = x + 1")
    with do_pdb_test(command) as output1:
        f(0)
    handler1.remove()

    handler2 = dowhen.when(f, "x = x + 1").bp()
    with do_pdb_test(command) as output2:
        f(0)
    handler2.remove()

    for out in (output1.getvalue(), output2.getvalue()):
        assert "x = x + 1" in out
        assert "(Pdb) " in out
        assert "test_bp()" in out
        assert "return x" in out
