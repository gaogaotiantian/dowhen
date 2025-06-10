# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import functools
import inspect


def get_line_number(code, identifier):
    if not isinstance(identifier, (list, tuple)):
        identifier = [identifier]

    agreed_line_number = None

    for ident in identifier:
        if isinstance(ident, int):
            line_number = ident
        elif isinstance(ident, str):
            if ident.startswith("+") and ident[1:].isdigit():
                line_number = code.co_firstlineno + int(ident[1:])
            else:
                lines, start_line = inspect.getsourcelines(code)
                for i, line in enumerate(lines):
                    if line.strip().startswith(ident):
                        line_number = start_line + i
                        break
                else:
                    return None
        else:
            raise TypeError(f"Unknown identifier type: {type(ident)}")

        if agreed_line_number is None:
            agreed_line_number = line_number
        elif agreed_line_number != line_number:
            return None

    if agreed_line_number is not None:
        if agreed_line_number not in (line[2] for line in code.co_lines()):
            # Need to check if agreed_line_number is indeed in the code object
            return None

    return agreed_line_number


@functools.lru_cache(maxsize=256)
def get_func_args(func):
    return inspect.getfullargspec(func).args


def call_in_frame(func, frame):
    f_locals = frame.f_locals
    args = []
    for arg in get_func_args(func):
        if arg == "_frame":
            args.append(frame)
            continue
        if arg not in f_locals:
            raise TypeError(f"Argument '{arg}' not found in frame locals.")
        args.append(f_locals[arg])
    return func(*args)
