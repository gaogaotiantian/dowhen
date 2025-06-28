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
    code: CodeType, identifier: int | str | re.Pattern | tuple
) -> list[int] | None:
    if not isinstance(identifier, tuple):
        identifier = (identifier,)

    line_numbers_sets = []

    for ident in identifier:
        if isinstance(ident, int):
            line_numbers_sets.append({ident})
        else:
            # We need source lines here
            try:
                lines, start_line = inspect.getsourcelines(code)
            except OSError:
                lines, start_line = None, code.co_firstlineno

            if isinstance(ident, str) and ident.startswith("+") and ident[1:].isdigit():
                # We need to find the actual definition of the function/class
                # when it is decorated
                if lines is None:
                    firstlineno = code.co_firstlineno
                else:
                    for idx, line in enumerate(lines):
                        # Skip all the decorators
                        if not line.strip().startswith("@"):
                            break
                    firstlineno = start_line + idx
                line_numbers_sets.append({firstlineno + int(ident[1:])})
            elif isinstance(ident, str) or isinstance(ident, re.Pattern):
                if lines is None:
                    return None
                line_numbers = set()
                for i, line in enumerate(lines):
                    line = line.strip()
                    if (isinstance(ident, str) and line.startswith(ident)) or (
                        isinstance(ident, re.Pattern) and ident.match(line)
                    ):
                        line_number = start_line + i
                        line_numbers.add(line_number)
                line_numbers_sets.append(line_numbers)
            else:
                raise TypeError(f"Unknown identifier type: {type(ident)}")

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
