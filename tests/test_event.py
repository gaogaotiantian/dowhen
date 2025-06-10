# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import pytest

import dowhen


def test_event_line_number():
    def f():
        pass

    target_line_number = f.__code__.co_firstlineno + 1

    for entity in (f, f.__code__):
        for identifier in [target_line_number, "+1", "pass", ("+1", "pass")]:
            event = dowhen.when(entity, identifier)
            assert event.event_type == "line"
            assert event.event_data["line_number"] == target_line_number

    with pytest.raises(ValueError):
        dowhen.when(f, "nonexistent")

    with pytest.raises(ValueError):
        dowhen.when(f, ("+3", "pass"))


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

    start_event = dowhen.when(f, "<start>")
    assert start_event.event_type == "start"
    assert start_event.event_data == {}
    handler = start_event.do("x = 1")
    assert f(2) == 1
    handler.remove()
    assert f(2) == 2

    return_event = dowhen.when(f, "<return>")
    assert return_event.event_type == "return"
    assert return_event.event_data == {}
    return_value = None

    def return_event_handler():
        nonlocal return_value
        return_value = 42

    handler = return_event.do(return_event_handler)
    f(0)
    assert return_value == 42
    return_value = 0
    handler.remove()
    f(0)
    assert return_value == 0


def test_goto():
    def f():
        x = 0
        assert False
        x = 1
        return x

    dowhen.when(f, "assert False").goto("x = 1")
    assert f() == 1


def test_invalid_type():
    def f():
        pass

    with pytest.raises(TypeError):
        dowhen.when(123, 1)

    with pytest.raises(TypeError):
        dowhen.when(f, 1.5)
