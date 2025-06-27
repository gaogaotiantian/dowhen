Usage Guide
===========

This guide provides comprehensive information on how to use dowhen for instrumentation.

Basic Concepts
--------------

An instrumentation is basically a callback on a trigger. You can think of ``do`` as a callback, and ``when`` as a trigger.

Triggers
--------

``when``
~~~~~~~~

``when`` takes an ``entity``, optional positional ``identifiers`` and an optional keyword-only ``condition``.

* ``entity`` - a function, method, code object, class, module or ``None``
* ``identifiers`` - something to locate a specific line or a special event
* ``condition`` - an expression or a function to determine whether the trigger should fire

Entity
^^^^^^

You need to specify an entity to instrument. This can be a function, method, code object, class, module or ``None``.

If you pass a class or module, dowhen will instrument all functions and methods in that class or module.

If you pass ``None``, ``dowhen`` will instrument globally, which means every code object will be instrumented.
This will introduce an overhead at the beginning, but the unnecessary events will be disabled while the
program is running.

Identifiers
^^^^^^^^^^^

Line
""""

To locate a line, you can use the absolute line number, a string starting with ``+`` as
the relative line number, or the prefix of the line.

.. code-block:: python

   from dowhen import when

   def f(x):
       return x  # line 4

   # These will all locate line 4
   when(f, 4)  # absolute line number
   when(f, "+1")  # relative to function start
   when(f, "return x")  # exact match of the line content
   when(f, "ret")  # prefix of the line

If an identifier matches multiple lines, the callback will trigger on all of them.

.. code-block:: python

   def f(x):
       x += 0
       x += 0
       return x

   do("x += 1").when(f, "x +=")  # triggers on both lines
   assert f(0) == 2

Special Events
""""""""""""""

Besides locating lines, you can also use special events as identifiers:

* ``"<start>"`` - when the function is called
* ``"<return>"`` - when the function returns

.. code-block:: python

   when(f, "<start>")    # triggers when f is called
   when(f, "<return>")  # triggers when f returns

Combination of Identifiers
""""""""""""""""""""""""""

You can combine multiple identifiers to make the trigger more specific:

.. code-block:: python

   when(f, ("return x", "+1"))  # triggers on `return x` only when it's the +1 line

Multiple identifiers
""""""""""""""""""""

You can also specify multiple identifiers to trigger on:

.. code-block:: python

   def f(x):
       for i in range(100):
           x += i
       return x

   do("print(x)").when(f, "return x", "<start>")  # triggers on both `return x` and when f is called

Conditions
^^^^^^^^^^

You can add conditions to triggers to make them more specific:

.. code-block:: python

   from dowhen import when

   def f(x):
       return x
    
   when(f, "return x", condition="x = 0").do("x = 1")
   assert f(0) == 1  # x is set to 1 when x is 0
   assert f(2) == 2  # x is not modified when x is not 0

You can also use a function as a condition:

.. code-block:: python

   from dowhen import when

   def f(x):
       return x

   def check(x):
       return x == 0

   when(f, "return x", condition=check).do("x = 1")
    
   when(f, "return x", condition=check).do("x = 1")
   assert f(0) == 1  # x is set to 1 when x is 0
   assert f(2) == 2  # x is not modified when x is not 0

If the condition function returns ``dowhen.DISABLE``, the trigger will not fire anymore.

.. code-block:: python

   from dowhen import when, DISABLE

   def f(x):
       return x

   def check(x):
       if x == 0:
           return True
       return DISABLE

   when(f, "return x", condition=check).do("x = 1")
    
   when(f, "return x", condition=check).do("x = 1")
   assert f(0) == 1  # x is set to 1 when x is 0
   assert f(2) == 2  # x is not modified and the trigger is disabled
   assert f(0) == 0  # x is not modified anymore

Source Hash
^^^^^^^^^^^

If you need to confirm that the source code of the function has not changed,
you can use the ``source_hash`` argument.

.. code-block:: python

   from dowhen import when, get_source_hash

   def f(x):
       return x

   # Calculate this once and use the constant in your code
   source_hash = get_source_hash(f)
   # This will raise an error if the source code of f changes
   when(f, "return x", source_hash=source_hash).do("x = 1")

``source_hash`` is not a security feature. It is just a sanity check to ensure
that the source code of the function has not changed so your instrumentation
is still valid. It's just the a piece of md5 has of the source code of the function.

Callbacks
---------

``do``
~~~~~~

``do`` executes code when the trigger fires, it can be a string or a function.

.. code-block:: python

   from dowhen import do

   def f(x):
       return x

   do("x = 1").when(f, "return x")
   assert f(0) == 1

If you are using a function for ``do``, the local variables that match the function arguments
will be automatically passed to the function.

Special arguments:

* ``_frame`` - when used, the current frame object is passed.
* ``_retval`` - when used, the return value of the function is passed. Only valid for ``<return>`` triggers.

If you want to change the value of the local variables, you need to return a dictionary
with the variable names as keys and the new values as values.

You can also return ``dowhen.DISABLE`` to disable the trigger.

.. code-block:: python

   from dowhen import do

   def f(x):
       return x

   def callback(x):
       return {"x": 1}

   do(callback).when(f, "return x")
   assert f(0) == 1

   def callback_special(_frame, _retval):
       assert _frame.f_locals["x"] == 1
       assert _retval == 1

   do(callback_special).when(f, "<return>")
   assert f(0) == 1

``bp``
~~~~~~

``bp`` enters pdb at the trigger.

.. code-block:: python

   from dowhen import bp

   def f(x):
       return x

   # Equivalent to setting a breakpoint at f
   bp().when(f, "<start>")

``goto``
~~~~~~~~

``goto`` can modify execution flow.

.. code-block:: python

   from dowhen import goto

   def f(x):
       x = 1
       return x

   # This skips the line `x = 1` and goes directly to `return x`
   goto("return x").when(f, "x = 1")
   assert f(0) == 0

Handlers
--------

When you combine a trigger with a callback, you create a handler.

.. code-block:: python

   from dowhen import when, do

   def f(x):
       return x

   # This creates a handler
   handler = when(f, "return x").do("x = 1")
   assert f(0) == 1  # x is set to 1 when f is called

   # You can temporarily disable the handler
   handler.disable()
   assert f(0) == 0  # x is not modified anymore

   # You can re-enable the handler
   handler.enable()
   assert f(0) == 1  # x is set to 1 again

   # You can also remove the handler permanently
   handler.remove()
   assert f(0) == 0  # x is not modified anymore

You can use ``with`` statement to create a handler that is automatically removed after the block:

.. code-block:: python

   from dowhen import do

   def f(x):
       return x

   with do("x = 1").when(f, "return x"):
       assert f(0) == 1
   assert f(0) == 0

``Handler`` can use ``do``, ``bp``, and ``goto`` as well, which allows you to
chain multiple callbacks together:

.. code-block:: python

   from dowhen import when

   def f(x):
       x += 100
       return x

   when(f, "x += 100").goto("return x").do("x += 1")
   assert f(0) == 1

Utilities
---------

clear_all
~~~~~~~~~

You can clear all handlers set by ``dowhen`` using ``clear_all``.

.. code-block:: python

   from dowhen import clear_all

   clear_all()
