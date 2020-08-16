#!/bin/env python3

from contextlib import contextmanager

import panopticon.version
from panopticon.trace import StreamingTrace
from panopticon.tracer import AsyncioTracer

__version__ = panopticon.version.version


@contextmanager
def trace(trace_file: str):
    with open(trace_file, "w") as out:
        with AsyncioTracer(trace=StreamingTrace(out)):
            yield
