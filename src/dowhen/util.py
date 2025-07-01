# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE


from __future__ import annotations

import functools
import inspect
import re
from collections.abc import Callable
from types import CodeType, FrameType, FunctionType, MethodType, ModuleType
from typing import Any

ident_with_offset = re.compile(r"(.+)(<<|>>)(\d+)$")


@functools.lru_cache(maxsize=256)
def get_line_numbers(
    code: CodeType, identifier: int | str | re.Pattern | tuple
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

    for ident in identifier:
        if isinstance(ident, int):
            line_numbers = {ident}
        elif isinstance(ident, str):
            if ident.startswith("+") and ident[1:].isdigit():
                line_numbers = {start_line + int(ident[1:])}
            else:
                if _m := ident_with_offset.match(ident):
                    _ident, _sign, _offset = _m.groups()
                    _offset = int(_offset) * int(_sign == ">>")
                else:
                    _ident = ident
                    _offset = 0
                line_numbers = {
                    start_line + i + _offset
                    for i, line in enumerate(lines)
                    if line.strip().startswith(_ident)
                }
        elif isinstance(ident, re.Pattern):
            line_numbers = {
                start_line + i
                for i, line in enumerate(lines)
                if ident.match(line.strip())
            }
        else:
            raise TypeError(f"Unknown identifier type: {type(ident)}")
        if not line_numbers:
            return None
        line_numbers_sets.append(line_numbers)

    agreed_line_numbers = set.intersection(*line_numbers_sets)
    agreed_line_numbers = {
        line_number
        for line_number in agreed_line_numbers
        if line_number in (line[2] for line in code.co_lines())
    }
    if not agreed_line_numbers:
        return None

    return sorted(agreed_line_numbers)


@functools.lru_cache(maxsize=256)
def get_func_args(func: Callable) -> list[str]:
    args = inspect.getfullargspec(inspect.unwrap(func)).args
    # For bound methods, skip the first argument since it's already bound
    if inspect.ismethod(func):
        return args[1:]
    else:
        return args


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
