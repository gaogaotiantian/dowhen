# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE


from __future__ import annotations

import functools
import inspect
import re
from collections.abc import Callable
from types import CodeType, FrameType, FunctionType, MethodType, ModuleType
from typing import Any


@functools.lru_cache(maxsize=256)
def get_line_numbers(
    code: CodeType,
    identifier: int | str | re.Pattern | tuple,
    base_start_line: int | None = None,
) -> list[int] | None:
    if not isinstance(identifier, tuple):
        identifier = (identifier,)

    line_numbers_sets = []

    try:
        lines, start_line = inspect.getsourcelines(code)
        # We need to find the actual definition of the function/class
        # when it is decorated
        while lines[0].strip().startswith("@"):
            # If the first line is a decorator, we need to skip it
            # and move to the next line
            lines.pop(0)
            start_line += 1
    except OSError:
        lines, start_line = [], code.co_firstlineno

    code_line_numbers = set(line[2] for line in code.co_lines())

    for ident in identifier:
        if isinstance(ident, int):
            line_numbers = {ident}
        else:
            if isinstance(ident, str) and ident.startswith("+") and ident[1:].isdigit():
                relative_offset = int(ident[1:])
                # Use base_start_line if provided, otherwise use current code's start_line
                reference_start_line = (
                    base_start_line if base_start_line is not None else start_line
                )
                target_line = reference_start_line + relative_offset
                if target_line in code_line_numbers:
                    line_numbers = {target_line}
                else:
                    return None
            elif isinstance(ident, str) or isinstance(ident, re.Pattern):
                line_numbers = set()
                for i, line in enumerate(lines):
                    line = line.strip()
                    if (isinstance(ident, str) and line.startswith(ident)) or (
                        isinstance(ident, re.Pattern) and ident.match(line)
                    ):
                        line_number = start_line + i
                        line_numbers.add(line_number)
            else:
                raise TypeError(f"Unknown identifier type: {type(ident)}")

        if not line_numbers:
            return None
        line_numbers_sets.append(line_numbers)

    agreed_line_numbers = set.intersection(*line_numbers_sets)
    # Filter out line numbers that are not in the code object
    agreed_line_numbers = {
        line_number
        for line_number in agreed_line_numbers
        if line_number in code_line_numbers
    }
    if not agreed_line_numbers:
        return None

    return sorted(agreed_line_numbers)


@functools.lru_cache(maxsize=256)
def get_base_start_line(code: CodeType) -> int:
    """Get the base start line number for a code object, handling decorators."""
    try:
        lines, start_line = inspect.getsourcelines(code)
        while lines and lines[0].strip().startswith("@"):
            lines.pop(0)
            start_line += 1
        return start_line
    except OSError:
        return code.co_firstlineno


@functools.lru_cache(maxsize=256)
def get_func_args(func: Callable) -> list[str]:
    return inspect.getfullargspec(func).args


def call_in_frame(func: Callable, frame: FrameType, **kwargs) -> Any:
    f_locals = frame.f_locals
    args = []
    for arg in get_func_args(func):
        if arg == "_frame":
            argval = frame
        elif arg == "_retval":
            if "retval" not in kwargs:
                raise TypeError("You can only use '_retval' in <return> callbacks.")
            argval = kwargs["retval"]
        elif arg in f_locals:
            argval = f_locals[arg]
        else:
            raise TypeError(f"Argument '{arg}' not found in frame locals.")
        args.append(argval)
    return func(*args)


def get_source_hash(entity: CodeType | FunctionType | MethodType | ModuleType | type):
    import hashlib

    source = inspect.getsource(entity)
    return hashlib.md5(source.encode("utf-8")).hexdigest()[-8:]
