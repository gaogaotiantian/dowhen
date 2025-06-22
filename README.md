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
from dowhen import do

def f(x):
    return x

# Same as when(f, "return x").do("x = 1")!
do("x = 1").when(f, "return x")

assert f(0) == 1
```

An instrumentation is basically a callback on a trigger. You can think of
`do` as a callback, and `when` as a trigger.

See detailed documentation at https://dowhen.readthedocs.io/

## License

Copyright 2025 Tian Gao.

Distributed under the terms of the  [Apache 2.0 license](https://github.com/gaogaotiantian/dowhen/blob/master/LICENSE).
