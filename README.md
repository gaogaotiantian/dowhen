# dowhen

`dowhen` makes instrumentation (monkeypatch) much more intuitive and maintainable!

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

An instrumentation is basically a callback on an event. You can think of
`do` as a callback, and `when` as an event.

## Event

An event is a specific time to trigger the callback.

### `when`

`when` takes an `entity`, an `identifier` and an optional `condition`.

* `entity` - a function, method or code object
* `identifier` - something to locate a specific line or a special event
* `condition` - an expression or a function to determine whether the event should fire

#### `identifier`

To locate a line, you can use the absolute line number, an string starting
with `+` as the relative line number, or the prefix of the line.

```python
from dowhen import when

def f(x):
    return x  # line 4

# These will all locate line 4
when(f, 4)
when(f, "+1")
when(f, "ret")
when(f, "return x")
```

Or you can fire the callback at special events like function start/return

```python
when(f, "<start>")
when(f, "<return>")
```

#### condition

`condition` takes a string expression or a function that evaluates to a
`bool`. It will be evaluated for every event and the event will only
fire when `condition` evaluates to `True`.

If a function is used, the magic local variable mapping as `do`
will also be applied.

```python
from dowhen import when

def f(x):
    return x

# Same as when(f, "return x", condition=lambda x: x == 0).do("x = 1")
when(f, "return x", condition="x == 0").do("x = 1")

assert f(0) == 1
assert f(2) == 2
```

## Callback

A callback is some action you want to perform at the event

### Do

`do` is to run some code at the event. It can take either a string
or a function.

```python
from dowhen import do

def print_callback(x):
    print(x)

# They are equivalent
do("print(x)")
do(print_callback)

def change_callback(x):
    return {"x": 1}

# They are equivalent
do("x = 1")
do(change_callback)
```

Notice that there are some black magic behind the scene if you use function
callback.

Local variables will be automatically passed as the arguments to the function
if they have the same names as the parameters.

If you need to change the local variables, you need to return a dictionary
with the local variable name as the key and the new value as the value.

#### Special Parameter

* `_frame` will take the frame object of the instrumented code

```python
def callback(_frame):
    # _frame has the frame of the instrumented code
    # _frame.f_locals is the locals of the actual function
    print(_frame.f_locals)
do(callback)
```

### goto

`goto` changes the next line to execute. It takes the same argument as the
`identifier` of `when` for line events.

```python
def f():
    assert False
    return 0

goto("return 0").when(f, "assert False")
# This skips `assert False`
f()
```

## Handler

When you combine an event with a callback, you get a handler.

```python
from dowhen import do, when

def f(x):
    return x

handler1 = do("x = 1").when(f, "return x")
handler2 = when(f, "<return>").do("print(x)")

# prints 1
f(0)
```

You don't have to save the handler, as long as you execute a `do().when`
or `when().do()`, the instrumentation is done. However, you can disable
and remove the instrumentation with the returned handler.

```python
handler1.disable()
assert f(0) == 0
handler1.enable()
assert f(0) == 1

# No output anymore
handler2.remove()
```

Or you can remove all the instrumentation by

```python
from dowhen import clear_all
clear_all()
```

## FAQ

#### Why we need this?

You can use `dowhen` anytime you need some different behavior but can't easily change the code.

For example:

* Debugging installed packages or Python stdlib
* Monkeypatching 3rd party libraries to support you stuff
* Avoid vendering and maintaining a library in production


#### Is the overhead very high?

No, it's actually super fast and can be used in production. Only the code object that
requires instrumentation gets instrumented, all the other code just runs exactly the same.

#### What's the mechanism behind it?

`dowhen` is based on `sys.monitoring` which was introduced in 3.12, which allows code object
based instrumentation, providing much finer granularity than the old `sys.settrace`.

That means `dowhen` does not actually change your code, which is much safer, but it won't
be able to instrument functions used in other instrumentation tools (nested instrumentation).

That also means `dowhen` can only be used in 3.12+.

#### I have a scenario but `dowhen` does not seem to support it.

Raise an issue, I'll see what I can do.

## License

Copyright 2025 Tian Gao.

Distributed under the terms of the  [Apache 2.0 license](https://github.com/gaogaotiantian/dowhen/blob/master/LICENSE).
