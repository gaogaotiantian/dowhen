Frequently Asked Questions
==========================

When do we need this?
---------------------

``dowhen`` serves well in these scenarios:

1. **monkeypatching**:

``down`` allows you to inject code at specific points in your application
without modifying the original codebase. When you need to change the behavior
of stdlib or third-party libraries, you can use `dowhen` to do it to
avoid vendoring your own version or swapping the whole function.

2. **debugging**:

``dowhen`` is just like a debugger - it can print stuff or execute code
at specific points in your code to help you understand what is going on.
Unlike a debugger, it is easily reproducible - you don't need to type
commands in a terminal.

3. **logging**:

``dowhen`` can be used to log all kinds of stuff without adding extra
code to your application.

Is the overhead high?
----------------------

Not at all. ``dowhen`` utilities ``sys.monitoring`` so it only triggers
events when necessary. It has minimal impacts on performance.

Why 3.12+?
----------

``dowhen`` uses the new `sys.monitoring` module introduced in Python 3.12,
