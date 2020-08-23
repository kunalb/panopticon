#!/bin/env python3

"""
WARNING: EXPERIMENTAL

Exploring a new API to trace specific functions and classes
"""

import inspect
import sys
import warnings
from functools import update_wrapper
from typing import Any, Callable, TypeVar

from panopticon.trace import Trace
from panopticon.tracer import AsyncioTracer, FunctionTracer

F = TypeVar("F", bound=Callable[..., Any])


def probe(trace: Trace) -> Callable:
    """Decorator to instrument functions and classes"""

    def decorator(o):
        if inspect.isclass(o):
            for method_name, method in vars(o).items():
                if callable(method):
                    setattr(
                        o,
                        method_name,
                        update_wrapper(_inner_probe(trace, method), method),
                    )
            return o
        else:  # Treat it as a function
            return update_wrapper(_inner_probe(trace, o), o)

    return decorator


def _inner_probe(trace, f):
    def wrapper(*args, **kwargs):
        current_frame = inspect.currentframe()

        def capture_args(frame, event, arg):
            return frame.f_back == current_frame

        outer_tracer = _OuterFrameTracer(trace)
        inner_tracer = _InnerFrameTracer(trace, capture_args)

        if _is_probe_active(trace):
            return f(*args, **kwargs)

        _emit_call(outer_tracer, current_frame)
        try:
            with inner_tracer:
                return f(*args, **kwargs)
        finally:
            _emit_return(outer_tracer, current_frame)

    return wrapper


class _OuterFrameTracer(FunctionTracer):
    def start(self):
        sys.setprofile(self)
        return self

    def stop(self):
        sys.setprofile(None)

    def _name(self, frame, event, arg):
        return "<<< " + super()._name(frame, event, arg) + " >>>"


class _InnerFrameTracer(AsyncioTracer):
    def start(self):
        sys.setprofile(self)
        return self

    def stop(self):
        sys.setprofile(None)


def _is_probe_active(current_trace) -> bool:
    """Check if another probe is already rendering"""
    current_profiler = sys.getprofile()
    is_active = isinstance(current_profiler, _InnerFrameTracer)

    if is_active and current_profiler.get_trace() != current_trace:
        warnings.warn(
            "Multiple traces from overlapping probes aren't supported!",
            RuntimeWarning,
        )

    return is_active


def _emit_call(outer_tracer, frame):
    # Invert the stack
    stack = []
    while frame is not None:
        stack.append(frame)
        frame = frame.f_back

    while stack:
        frame = stack.pop()
        outer_tracer(frame, "call", None)


def _emit_return(outer_tracer, frame):
    while frame:
        outer_tracer(frame, "return", None)
        frame = frame.f_back
