#!/bin/env python3

"""
A lighter probe implementation.
"""

import collections
import inspect
from functools import update_wrapper
from panopticon.trace import DurationTraceEvent, Phase, Trace
from typing import Callable

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
            return

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
                tracer._fn_cat(x)
            )
        finally:
            tracer.return_fn(x, None)
            tracer.return_backtrace(inspect.currentframe())
            
    return wrapper


class _CoroutineProbe(collections.abc.Coroutine):

    def __init__(self, tracer, x, cat):
        self._tracer = tracer
        self._x = x
        self._cat = cat

    def send(self, val):
        self._x.send(val)

    def throw(self, typ, val=None, tb=None):
        self._x.throw(typ, val, tb)

    def close(self):
        self._x.close()

    def __await__(self):
        try:
            while True:
                self._tracer.call_backtrace(inspect.currentframe())
                self._tracer.call_fn(self._x, [], {}, cat=self._cat)
                try:
                    result = self._x.send(None)
                    yield result
                except StopIteration as stop:
                    self._tracer.return_fn(self._x, stop.value, cat=self._cat)
                    raise StopIteration
                except:
                    self._tracer.return_fn(self._x, result, cat=self._cat)
                    raise
                else:
                    self._tracer.return_fn(self._x, result, cat=self._cat)
                finally:
                    self._tracer.return_backtrace(inspect.currentframe())
        except StopIteration:
            ...


def _probe_async_generator(tracer, x):
    ...


def _probe_function(tracer, x):
    def wrapper(*args, **kwargs):
        tracer.call_backtrace(inspect.currentframe())
        tracer.call_fn(x, args, kwargs)

        return_value = None
        try:
            return_value = x(*args, **kwargs)
            return return_value
        finally:
            tracer.return_fn(x, return_value)
            tracer.return_backtrace(inspect.currentframe())

    return wrapper

class _Tracer(FunctionTracer):
    def start(self):
        return self

    def stop(self):
        ...

    def call_fn(self, fn, args, kwargs, cat=None):
        self._trace.add_event(
            DurationTraceEvent(
                name=str(fn),
                cat=cat or self._fn_cat(fn),
                ph=Phase.Duration.START,
                args=self._fn_args(args, kwargs)
            )
        )

    def return_fn(self, fn, return_value, cat=None):
        self._trace.add_event(
            DurationTraceEvent(
                name=str(fn),
                cat=cat or self._fn_cat(fn),
                ph=Phase.Duration.END,
                args={self._RETURN_KEY: repr(return_value)}
            )
        )

    @staticmethod
    def _fn_cat(fn):
        code = fn.__code__
        return f"{code.co_filename}:{code.co_firstlineno}"

    @staticmethod
    def _fn_args(args, kwargs):
        # TODO Apply https://stackoverflow.com/questions/42352703/get-names-of-positional-arguments-from-functions-signature
        # And get names for all the arguments
        result = {}
        for i, val in enumerate(args):
            result[i] = repr(val)
        for key, val in kwargs.items():
            result[key] = repr(val)
        return result

    def call_backtrace(self, frame):
        # Invert the stack
        stack = []
        while frame is not None:
            stack.append(frame)
            frame = frame.f_back

        while stack:
            frame = stack.pop()
            self(frame, "call", None)

    def return_backtrace(self, frame):
        while frame:
            self(frame, "return", None)
            frame = frame.f_back

    def _name(self, frame, event, arg):
        # Avoiding name cache
        return "... " + super()._get_frame_name(frame) + " ..."

