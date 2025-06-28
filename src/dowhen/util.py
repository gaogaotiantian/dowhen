# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE


from __future__ import annotations

import functools
import inspect
import re
import warnings
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
        else:
            if isinstance(ident, str) and ident.startswith("+") and ident[1:].isdigit():
                line_numbers = {start_line + int(ident[1:])}
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
    if lines:
        in_scope_line_numbers = agreed_line_numbers & set(
            range(start_line, start_line + len(lines))
        )
    else:
        in_scope_line_numbers = agreed_line_numbers

    executable_lines = {line[2] for line in code.co_lines() if line[2] is not None}

    valid_line_numbers = set()
    for line_number in in_scope_line_numbers:
        if line_number in executable_lines:
            valid_line_numbers.add(line_number)
            continue

        fallback_ln = min(
            (e_ln for e_ln in executable_lines if e_ln > line_number), default=None
        )

        if fallback_ln is None:
            raise ValueError(
                f"Line {line_number} in {code.co_filename} is not executable "
                "and no fallback line was found."
            )
        valid_line_numbers.add(fallback_ln)
        warnings.warn(
            f"Line {line_number} in {code.co_filename} is not executable. "
            f"Falling back to next executable line {fallback_ln}.",
            UserWarning,
            stacklevel=3,
        )

    if not valid_line_numbers:
        return None

    return sorted(valid_line_numbers)


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
