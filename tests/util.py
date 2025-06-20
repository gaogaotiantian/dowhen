# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/gaogaotiantian/dowhen/blob/master/NOTICE.txt


import contextlib


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
