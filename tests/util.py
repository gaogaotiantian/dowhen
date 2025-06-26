# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE


import contextlib
import io
import sys
import textwrap


@contextlib.contextmanager
def disable_coverage():
    try:
        import coverage

        cov = coverage.Coverage().current()
    except ModuleNotFoundError:
        cov = None

    if cov is None:
        yield
        return

    cov.stop()
    yield
    cov.start()


@contextlib.contextmanager
def do_pdb_test(command):
    command_input = io.StringIO(textwrap.dedent(command))
    output = io.StringIO()

    _stdin = sys.stdin
    _stdout = sys.stdout
    try:
        sys.stdin = command_input
        sys.stdout = output
        with disable_coverage():
            yield output
    finally:
        sys.stdin = _stdin
        sys.stdout = _stdout
