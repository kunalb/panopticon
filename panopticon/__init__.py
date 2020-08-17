#!/bin/env python3

"""Defines the external facing API for usage in code"""

from contextlib import contextmanager

import panopticon.version
import panopticon.trace
from panopticon.tracer import AsyncioTracer

__version__ = panopticon.version.version


@contextmanager
def trace(trace_file: str):
    with open(trace_file, "w") as out:
        with AsyncioTracer(trace=panopticon.trace.StreamingTrace(out)):
            yield
