# dowhen

`dowhen` makes instrumentation (monkeypatch) much more intuitive and maintainable!

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

```python
from dowhen import bp, do, goto, when

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

# bp() is another callback that brings up pdb
# You don't need to store the handler if you don't use it
handler = bp().when(f, "return x")
# This will enter pdb
f(0)
# You can temporarily disable the handler
# handler.enable() will enable it again
handler.disable()

# goto() is a callback too
# This will skip the line of `x += 100`
# The handler will be removed after the context
with goto("return x").when(f, "x += 100"):
    assert f(0) == 0

# You can chain callbacks and they'll run in order
# You don't need to store the handler if you don't use it
when(f, "x += 100").goto("return x").do("x = 42")
assert f(0) == 42
```

See detailed documentation at https://dowhen.readthedocs.io/

## License

Copyright 2025 Tian Gao.

Distributed under the terms of the  [Apache 2.0 license](https://github.com/gaogaotiantian/dowhen/blob/master/LICENSE).
