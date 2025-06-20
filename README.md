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

An instrumentation is basically a callback on a trigger. You can think of
`do` as a callback, and `when` as a trigger.

## Trigger

### `when`

`when` takes an `entity`, optional positional `identifiers` and
an optional keyword-only `condition`.

* `entity` - a function, method, code object, class or module
* `identifiers` - something to locate a specific line or a special event
* `condition` - an expression or a function to determine whether the trigger should fire

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

You can combine these identifiers together as a tuple to construct an `and` logic.

```python
# This works!
when(f, (4, "+1"))

# This will raise an error! Helpful to catch source line changes
when(f, (4, "+2"))
```

A special case would be when you want to trigger the event on every line.
Then you don't need to pass any identifier

```python
def f(x):
    x = 1
    x = 2
    return x

# Will print 0, 1, 2 in each line
do("print(x)").when(f)
f(0)
```

Or you can fire the callback at special events like function start/return

```python
when(f, "<start>")
when(f, "<return>")
```

You can also pass multiple identifiers to construct an `or` logic.

```python
def f(x):
    for i in range(100):
        # very noisy
        x += i
    return x

# print before and after for loop
do("print(x)").when(f, "<start>", "return x")
f(3)
```

#### condition

`condition` takes a string expression or a function that evaluates to a
`bool`. It will be evaluated for every trigger and the trigger will only
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

A callback is some action you want to perform at the trigger

### Do

`do` is to run some code at the trigger. It can take either a string
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

### bp

`bp` (short for `breakpoint`) enters `pdb` at the trigger.

```python
from dowhen import bp

def f(x):
    return x

bp().when(f, "return x")
# enters pdb at `return x`
f(0)
```

## Handler

When you combine a trigger with a callback, you get a handler.

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
