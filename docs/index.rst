dowhen documentation
====================

``dowhen`` is an instrumentation tool for Python that allows you execute
certain code at specific triggers in a clean and maintainable way.

Installation
------------

.. code-block:: bash

   pip install dowhen

Quick Start
-----------

.. code-block:: python

   from dowhen import do, goto, bp

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
   # You don't need to store the handler if you don't use it
   goto("return x").when("x += 100")
   assert f(0) == 0

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   api
   faq

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
