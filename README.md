# dowhen

[![build](https://github.com/gaogaotiantian/dowhen/actions/workflows/build_test.yml/badge.svg)](https://github.com/gaogaotiantian/dowhen/actions/workflows/build_test.yml)
[![readthedocs](https://img.shields.io/readthedocs/dowhen)](https://dowhen.readthedocs.io/)
[![coverage](https://img.shields.io/codecov/c/github/gaogaotiantian/dowhen)](https://codecov.io/gh/gaogaotiantian/dowhen)
[![pypi](https://img.shields.io/pypi/v/dowhen.svg)](https://pypi.org/project/dowhen/)
[![support-version](https://img.shields.io/pypi/pyversions/dowhen)](https://img.shields.io/pypi/pyversions/dowhen)
[![sponsor](https://img.shields.io/badge/%E2%9D%A4-Sponsor%20me-%23c96198?style=flat&logo=GitHub)](https://github.com/sponsors/gaogaotiantian)

`dowhen` makes instrumentation (monkeypatch) super intuitive and maintainable
with minimal overhead!

You can execute arbitrary code at specific points of your application,
third-party libraries or stdlib in order to

* debug your program
* change the original behavior of the libraries
* monitor your application

## Installation

```
pip install dowhen
```

## Usage

The core idea behind `dowhen` is to do a *callback* on a *trigger*. The
*trigger* is specified with `when` and there are 3 kinds of *callbacks*.

### do

`do` executes an arbitrary piece of code.

```python
from dowhen import do

def f(x):
    x += 100
    # Let's change the value of x before return
    return x

# do("x = 1") is the callback
# when(f, "return x") is the trigger
# This is equivalent to:
# handler = when(f, "return x").do("x = 1")
handler = do("x = 1").when(f, "return x")
# x = 1 is executed before "return x"
assert f(0) == 1

# You can remove the handler
handler.remove()
assert f(0) == 100
```

### bp

`bp` sets a breakpoint and brings up `pdb`.

```python
from dowhen import bp

# bp() is another callback that brings up pdb
handler = bp().when(f, "return x")
# This will enter pdb
f(0)
# You can temporarily disable the handler
# handler.enable() will enable it again
handler.disable()
```

### goto

`goto` changes the next line to execute.

```python
from dowhen import goto

# This will skip the line of `x += 100`
# The handler will be removed after the with context
with goto("return x").when(f, "x += 100"):
    assert f(0) == 0
```

### callback chains

```python
from dowhen import when

# You can chain callbacks and they'll run in order at the trigger
# You don't need to store the handler if you don't use it
when(f, "x += 100").goto("return x").do("x = 42")
assert f(0) == 42
```

See detailed documentation at https://dowhen.readthedocs.io/

## License

Copyright 2025 Tian Gao.

Distributed under the terms of the  [Apache 2.0 license](https://github.com/gaogaotiantian/dowhen/blob/master/LICENSE).
