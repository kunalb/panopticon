#!/bin/env python3

"""
WARNING: EXPERIMENTAL

Exploring a new API to trace specific functions and classes
"""

import inspect
import io
import sys
from typing import Any, Callable, Optional, TypeVar

from panopticon.trace import StreamingTrace, Trace
from panopticon.tracer import AsyncioTracer, FunctionTracer

F = TypeVar("F", bound=Callable[..., Any])


class _IncompleteFrameTracer(FunctionTracer):
    def start(self):
        sys.setprofile(self)
        return self

    def stop(self):
        sys.setprofile(None)

    @classmethod
    def _name(self, code):
        return "<<< " + super()._name(code) + " >>>"


class _InnerFrameTracer(AsyncioTracer):
    def start(self):
        sys.setprofile(self)
        return self

    def stop(self):
        sys.setprofile(None)


class Probe:
    """Inserted into code when establishing a panopticon isn't possible"""

    def __init__(self, f: Callable[..., Any], trace: Trace) -> None:
        self._f = f
        self._tracer = _IncompleteFrameTracer(trace=trace)
        self._inner_tracer = _InnerFrameTracer(trace=trace)

    def get_trace(self) -> Trace:
        return self._tracer.get_trace()

    def __call__(self, *args, **kwargs):
        # Capture arguments and log as additional values
        # Capture return value and log as additional values

        self._emit_call(inspect.currentframe())
        try:
            with self._inner_tracer:
                return self._f(*args, **kwargs)
        finally:
            self._emit_return(inspect.currentframe())

    def _emit_call(self, frame):
        # Invert the stack
        stack = []
        while frame is not None:
            stack.append(frame)
            frame = frame.f_back

        while stack:
            frame = stack.pop()
            self._tracer(frame, "call", None)

    def _emit_return(self, frame):
        while frame:
            self._tracer(frame, "return", None)
            frame = frame.f_back


def probe(
    file: Optional[io.IOBase] = None,
    callback: Optional[Callable[[str], None]] = None,
) -> F:
    """Decorator to instrument a specific function and visualize its calls"""

    if not file and not callback:
        raise ValueError("One of file or callback must be specified.")

    def decorator(f):
        """TODO Figure out how to wrap appropriately"""
        trace = StreamingTrace(file)
        probe = Probe(f, trace)
        return probe

    return decorator


def trace_class(c):
    """Decorator to instrument calls to *all* methods of a class"""

    return c
