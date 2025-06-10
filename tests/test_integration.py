# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


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
