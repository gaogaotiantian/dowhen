# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE


import functools
import re
import sys

import pytest

import dowhen


def test_event_line_number():
    def f():
        pass

    target_line_number = f.__code__.co_firstlineno + 1

    for entity in (f, f.__code__):
        for identifier in [
            target_line_number,
            "+1",
            "pass",
            ("+1", "pass"),
            re.compile(r"pass"),
        ]:
            trigger = dowhen.when(entity, identifier)
            assert trigger.events[0].event_type == "line"
            assert trigger.events[0].event_data["line_number"] == target_line_number

    with pytest.raises(ValueError):
        dowhen.when(f, "nonexistent")

    with pytest.raises(ValueError):
        dowhen.when(f, ("+3", "pass"))


def test_event_multiple_line_match():
    def f(x):
        x += 1
        x += 2
        return x

    dowhen.when(f, "x +=").do("x += 1")
    assert f(0) == 5


def test_when_do():
    def f(x):
        return x

    dowhen.when(f, "return x").do("x = 1")
    assert f(2) == 1
    dowhen.clear_all()
    assert f(2) == 2


def test_start_return():
    def f(x):
        return x

    start_trigger = dowhen.when(f, "<start>")
    assert start_trigger.events[0].event_type == "start"
    assert start_trigger.events[0].event_data == {}
    handler = start_trigger.do("x = 1")
    assert f(2) == 1
    handler.remove()
    assert f(2) == 2

    return_trigger = dowhen.when(f, "<return>")
    assert return_trigger.events[0].event_type == "return"
    assert return_trigger.events[0].event_data == {}
    return_value = None

    def return_event_handler():
        nonlocal return_value
        return_value = 42

    handler = return_trigger.do(return_event_handler)
    f(0)
    assert return_value == 42
    return_value = 0
    handler.remove()
    f(0)
    assert return_value == 0


def test_closure():
    def f(x):
        def g():
            return x

        return g()

    dowhen.when(f, "return x").do("x = 1")
    assert f(2) == 1


def test_method():
    class A:
        def f(self, x):
            return x

    a = A()
    dowhen.when(a.f, "return x").do("x = 1")
    assert a.f(2) == 1


def test_module():
    import random

    co_lines = random.randrange.__code__.co_lines()
    for _, _, lineno in co_lines:
        if lineno != random.randrange.__code__.co_firstlineno:
            first_line = lineno
            break
    assert isinstance(first_line, int)
    write_back = []
    dowhen.when(random, first_line).do(lambda: write_back.append(True))
    random.randrange(10)
    assert write_back == [True]


def test_class():
    class A:
        def f(self, x):
            return x

        def g(self, x):
            return x

    dowhen.when(A, "return x").do("x = 1")
    a = A()
    assert a.f(2) == 1
    assert a.g(2) == 1


def test_decorator():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(x):
            return func(x)

        return wrapper

    @decorator
    def f(x):
        x += 1
        return x

    with dowhen.when(f, "return x").do("x = 42"):
        assert f(0) == 42

    with dowhen.when(f, "+1").do("x += 1"):
        assert f(0) == 2

    with dowhen.when(f, "+2").do("x = 42"):
        assert f(0) == 42

    @decorator
    def cond(x):
        return x > 1

    with dowhen.when(f, "return x", condition=cond).do("x = 42"):
        assert f(0) == 1
        assert f(1) == 42

    @decorator
    def cb(x):
        return {"x": 42}

    with dowhen.when(f, "return x").do(cb):
        assert f(0) == 42


def test_code_without_source():
    src = """def f(x):\n  return x\nf(0)"""
    code = compile(src, "<string>", "exec")
    events = []
    with dowhen.when(code, "+1").do(lambda: events.append(0)):
        exec(code)
        assert events == [0]


def test_every_line():
    def f(x):
        x = 1
        x = 2
        x = 3
        return x

    lst = []

    def cb(x):
        lst.append(x)

    dowhen.when(f).do(cb)
    f(0)
    assert lst == [0, 1, 2, 3]


def test_multiple_lines():
    def f(x):
        x = 1
        x = 2
        x = 3
        return x

    lst = []

    def cb(x):
        lst.append(x)

    dowhen.when(f, "x = 1", "x = 3").do(cb)
    f(0)
    assert lst == [0, 2]
    dowhen.clear_all()


def test_mix_events():
    def f(x):
        for i in range(100):
            x += i
        return x

    write_back = []
    dowhen.when(f, "<start>", "return x").do(lambda: write_back.append(1))
    f(0)
    assert write_back == [1, 1]


def test_global_events():
    def f(x):
        x += 1
        return x

    events = []

    def f_callback(_frame):
        if _frame.f_code.co_name == "f":
            events.append(0)

    with dowhen.when(None, "<start>").do(f_callback):
        f(0)

    with dowhen.when(None, "<return>").do(f_callback):
        f(0)

    with dowhen.when(None, "return").do(f_callback):
        f(0)

    assert events == [0, 0, 0]


def test_goto():
    def f():
        x = 0
        assert False
        x = 1
        return x

    dowhen.when(f, "assert False").goto("x = 1")
    assert f() == 1


def test_condition():
    def f(x):
        return x

    dowhen.when(f, "return x", condition="x == 0").do("x = 1")

    assert f(0) == 1
    assert f(2) == 2

    dowhen.clear_all()

    dowhen.when(f, "return x", condition=lambda x: x == 0).do("x = 1")
    assert f(0) == 1
    assert f(2) == 2

    dowhen.clear_all()

    with pytest.raises(ValueError):
        dowhen.when(f, "return x", condition="x ==")

    with pytest.raises(TypeError):
        dowhen.when(f, "return x", condition=1.5)


def test_source_hash():
    def f(x):
        return x

    source_hash = dowhen.get_source_hash(f)

    dowhen.when(f, "return x", source_hash=source_hash)

    with pytest.raises(ValueError):
        dowhen.when(f, "return x", source_hash=source_hash + "1")

    with pytest.raises(TypeError):
        dowhen.when(f, "return x", source_hash=123)


def test_should_fire():
    def f(x):
        return x

    frame = sys._getframe()

    for trigger in (
        dowhen.when(f, "return x", condition="x == 0"),
        dowhen.when(f, "return x", condition=lambda x: x == 0),
    ):
        x = 0
        assert trigger.should_fire(frame) is True
        x = 1
        assert trigger.should_fire(frame) is False
        del x
        assert trigger.should_fire(frame) is False


def test_has_event():
    def f(x):
        x += 1
        return x

    frame = sys._getframe()
    trigger = dowhen.when(None, "assert")
    assert trigger.has_event(frame) is True

    trigger = dowhen.when(None, "trigger")
    assert trigger.has_event(frame) is False

    trigger = dowhen.when(f, "return x")
    assert trigger.has_event(frame) is True


def test_invalid_type():
    def f():
        pass

    with pytest.raises(TypeError):
        dowhen.when(123, 1)

    with pytest.raises(TypeError):
        dowhen.when(f, 1.5)

    with pytest.raises(ValueError):
        dowhen.when(None, "return", source_hash="12345678")


def test_invalid_line_number():
    def f():
        pass

    with pytest.raises(ValueError):
        dowhen.when(f, 1000)

    with pytest.raises(ValueError):
        dowhen.when(f, "+1000")

    code = compile("pass", "<string>", "exec")
    with pytest.raises(ValueError):
        dowhen.when(code, "return")
