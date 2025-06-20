# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import inspect

import pytest

import dowhen


def test_clear_all():
    def f(x):
        return x

    dowhen.do("x = 1").when(f, "return x")
    dowhen.do("x = 1").when(f, "<start>")
    dowhen.do("x = 1").when(f, "<return>")

    assert f(2) == 1
    dowhen.clear_all()
    assert f(2) == 2


def test_multi_callback():
    def f(x, y):
        return x + y

    handler_x = dowhen.do("x = 1").when(f, "return x + y")
    handler_y = dowhen.do("y = 2").when(f, "return x + y")

    assert f(0, 0) == 3

    handler_x.remove()
    assert f(0, 0) == 2

    handler_y.remove()
    assert f(0, 0) == 0


def func_test(x, y):
    x = x + 1
    y = y + 1
    return x, y


@pytest.mark.parametrize(
    "cb_func, entity, identifiers, expected_results",
    [
        ("x = 2", func_test, ("return x",), ([0, 0], (2, 1))),
        ("x += 1", func_test, ("return x", "<start>"), ([0, 0], (3, 1))),
        ("x += 1", func_test, (), ([0, 0], (4, 1))),
    ],
)
def test_integration(cb_func, entity, identifiers, expected_results):
    args, retval = expected_results
    handler = dowhen.do(cb_func).when(entity, *identifiers)
    assert func_test(*args) == retval
    handler.remove()

    handler = dowhen.when(entity, *identifiers).do(cb_func)
    assert func_test(*args) == retval
    handler.remove()


def test_signature():
    def f():
        pass

    callback = dowhen.do("x = 1")
    trigger = dowhen.when(f)

    signature_pairs = [
        (callback.when, dowhen.when),
        (trigger.do, dowhen.do),
        (trigger.goto, dowhen.goto),
        (trigger.bp, dowhen.bp),
    ]
    for func1, func2 in signature_pairs:
        assert (
            inspect.signature(func1).parameters == inspect.signature(func2).parameters
        )
