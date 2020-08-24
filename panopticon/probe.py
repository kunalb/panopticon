#!/bin/env python3

"""
A lighter probe implementation.
"""

import collections
import inspect
import re
from functools import update_wrapper
from typing import Callable

from panopticon.trace import DurationTraceEvent, Phase, Trace
from panopticon.tracer import FunctionTracer


def probe(trace: Trace) -> Callable:
    tracer = _Tracer(trace)

    def decorator(x):
        if inspect.isclass(x):
            for method_name, method in vars(x).items():
                if callable(method):
                    setattr(
                        x, method_name, decorator(method),
                    )
            return x
        if inspect.isgeneratorfunction(x):
            replacement = _probe_generator(tracer, x)
        elif inspect.iscoroutinefunction(x):
            replacement = _probe_coroutine(tracer, x)
        elif inspect.isasyncgenfunction(x):
            replacement = _probe_async_generator(tracer, x)
        else:
            replacement = _probe_function(tracer, x)

        return update_wrapper(replacement, x)

    return decorator


def _probe_generator(tracer, x):
    ...


def _probe_coroutine(tracer, x):
    def wrapper(*args, **kwargs):
        tracer.call_backtrace(inspect.currentframe())
        tracer.call_fn(x, args, kwargs)

        try:
            return _CoroutineProbe(
                tracer,
                x(*args, **kwargs),
                tracer._fn_name(x),
                tracer._fn_cat(x),
            )
        finally:
            tracer.return_fn(x, None)
            tracer.return_backtrace(inspect.currentframe())

    return wrapper


class _CoroutineProbe(collections.abc.Coroutine):
    def __init__(self, tracer, x, name, cat):
        self._tracer = tracer
        self._x = x
        self._trace_args = {"name": name, "cat": cat}

    def send(self, val):
        # TODO Instrument
        self._x.send(val)

    def throw(self, typ, val=None, tb=None):
        # TODO Instrument
        self._x.throw(typ, val, tb)

    def close(self):
        # TODO Instrument
        self._x.close()

    def __await__(self):
        __panopticon_marker = self._tracer

        while True:
            self._tracer.call_backtrace(inspect.currentframe())
            self._tracer.event(ph=Phase.Duration.START, **self._trace_args)
            try:
                result = self._x.send(None)
                yield result
            except StopIteration as stop:
                self._tracer.event(
                    ph=Phase.Duration.END,
                    args={self._tracer._RETURN_KEY: repr(stop.value)},
                    **self._trace_args,
                )
                break
            except:
                self._tracer.event(
                    ph=Phase.Duration.END, **self._trace_args,
                )
                raise
            else:
                self._tracer.event(
                    ph=Phase.Duration.END,
                    args={self._tracer._RETURN_KEY: repr(result)},
                    **self._trace_args,
                )
            finally:
                self._tracer.return_backtrace(inspect.currentframe())


def _probe_async_generator(tracer, x):
    ...


def _probe_function(tracer, x):
    def wrapper(*args, **kwargs):
        __panopticon_marker = tracer

        frame = inspect.currentframe()
        tracer.call_backtrace(frame)
        tracer.call_fn(x, args, kwargs)

        return_value = None
        try:
            return_value = x(*args, **kwargs)
            return return_value
        finally:
            tracer.return_fn(x, return_value)
            tracer.return_backtrace(frame)

    return wrapper


class _Tracer(FunctionTracer):
    """TODO Refactor/simplify this class"""

    _FN_REGEX = re.compile(r"<function (.*?) at 0x[^ ]+>")

    def start(self):
        return self

    def stop(self):
        ...

    def call_fn(self, fn, args, kwargs):
        self.event(
            name=self._fn_name(fn),
            cat=self._fn_cat(fn),
            ph=Phase.Duration.START,
            args=self._fn_args(fn, args, kwargs),
        )

    def return_fn(self, fn, return_value):
        self.event(
            name=self._fn_name(fn),
            cat=self._fn_cat(fn),
            ph=Phase.Duration.END,
            args={self._RETURN_KEY: repr(return_value)},
        )

    def event(self, name, cat, ph, args=None):
        self._trace.add_event(
            DurationTraceEvent(name=name, cat=cat, ph=ph, args=args,)
        )

    @classmethod
    def _fn_name(cls, fn):
        return cls._FN_REGEX.search(str(fn)).group(1)

    @staticmethod
    def _fn_cat(fn):
        code = fn.__code__
        return f"{code.co_filename}:{code.co_firstlineno}"

    @staticmethod
    def _fn_args(fn, args, kwargs):
        bound_arguments = inspect.signature(fn).bind(*args, **kwargs)
        result = {}
        for key, val in bound_arguments.arguments.items():
            result[key] = repr(val)
        return result

    def call_backtrace(self, frame):
        # Invert the stack
        stack = []
        while frame is not None and not self._is_traced_frame(frame):
            stack.append(frame)
            frame = frame.f_back

        while stack:
            frame = stack.pop()
            self(frame, "call", None)

    def return_backtrace(self, frame):
        while frame and not self._is_traced_frame(frame):
            self(frame, "return", None)
            frame = frame.f_back

    def _is_traced_frame(self, frame):
        return (
            frame is not None
            and frame.f_back is not None
            and frame.f_back.f_locals.get("__panopticon_marker")
            and frame.f_back.f_locals.get("__panopticon_marker").get_trace()
            == self.get_trace()
        )

    def _name(self, frame, event, arg):
        # Avoiding name cache
        return "... " + super()._get_frame_name(frame) + " ..."
