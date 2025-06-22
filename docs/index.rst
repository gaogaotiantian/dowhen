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

   from dowhen import do

   def f(x):
       return x

   # Same as when(f, "return x").do("x = 1")!
   do("x = 1").when(f, "return x")

   assert f(0) == 1

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
