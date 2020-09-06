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
    def wrapper(*args, **kwargs):
        _panopticon_marker = tracer  # noqa: F841
        tracer.call_backtrace(inspect.currentframe())
        tracer.call_fn(x, args, kwargs)

        try:
            return _GeneratorProbe(
                tracer,
                x(*args, **kwargs),
                tracer._fn_name(x),
                tracer._fn_cat(x),
            )
        finally:
            tracer.return_fn(x, None)
            tracer.return_backtrace(inspect.currentframe())

    return wrapper


class _GeneratorProbe(collections.abc.Generator):
    def __init__(self, tracer, x, name, cat):
        self._tracer = tracer
        self._x = x
        self._trace_args = {"name": name, "cat": cat}

    def send(self):
        return self._x.send()

    def throw(self):
        return self._x.throw()

    def __next__(self):
        _panopticon_marker = self._tracer  # noqa: F841
        self._tracer.call_backtrace(inspect.currentframe())
        self._tracer.event(ph=Phase.Duration.START, **self._trace_args)

        return_value = None
        try:
            return_value = self._x.send(None)
            return return_value
        finally:
            self._tracer.event(
                ph=Phase.Duration.END,
                args={
                    self._tracer._RETURN_KEY: self._tracer._safe_repr(
                        self._tracer._RETURN_KEY, return_value
                    )
                },
                **self._trace_args,
            )
            self._tracer.return_backtrace(inspect.currentframe())


def _probe_coroutine(tracer, x):
    def wrapper(*args, **kwargs):
        _panopticon_marker = tracer  # noqa: F841
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
        _panopticon_marker = self._tracer  # noqa: F841
        it = self._x.__await__()

        while True:
            self._tracer.call_backtrace(inspect.currentframe())
            self._tracer.event(ph=Phase.Duration.START, **self._trace_args)
            try:
                result = next(it)
                yield result
            except StopIteration as stop:
                self._tracer.event(
                    ph=Phase.Duration.END,
                    args={
                        self._tracer._RETURN_KEY: self._tracer._safe_repr(
                            self._tracer._RETURN_KEY, stop.value
                        )
                    },
                    **self._trace_args,
                )
                break
            except:  # noqa: E722
                self._tracer.event(
                    ph=Phase.Duration.END, **self._trace_args,
                )
                raise
            else:
                self._tracer.event(
                    ph=Phase.Duration.END,
                    args={
                        self._tracer._RETURN_KEY: self._tracer._safe_repr(
                            self._tracer._RETURN_KEY, result
                        )
                    },
                    **self._trace_args,
                )
            finally:
                self._tracer.return_backtrace(inspect.currentframe())


def _probe_async_generator(tracer, x):
    def wrapper(*args, **kwargs):
        _panopticon_marker = tracer  # noqa: F841
        tracer.call_backtrace(inspect.currentframe())
        tracer.call_fn(x, args, kwargs)

        try:
            return _AsyncGeneratorProbe(
                tracer,
                x(*args, **kwargs),
                tracer._fn_name(x),
                tracer._fn_cat(x),
            )
        finally:
            tracer.return_fn(x, None)
            tracer.return_backtrace(inspect.currentframe())

    return wrapper


class _AsyncGeneratorProbe(collections.abc.AsyncGenerator):
    def __init__(self, tracer, x, name, cat):
        self._tracer = tracer
        self._x = x
        self._trace_args = {"name": name, "cat": cat}

    async def asend(self, value):
        return await self._x.asend(value)

    async def athrow(self, typ, val=None, tb=None):
        return await self._x.athrow(typ, val, tb)

    async def aclose(self):
        return await self._x.aclose()

    async def __anext__(self):
        probed = _CoroutineProbe(
            self._tracer, self._x.__anext__(), **self._trace_args
        )
        return await probed


def _probe_function(tracer, x):
    def wrapper(*args, **kwargs):
        _panopticon_marker = tracer  # noqa: F841

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
            args={
                self._RETURN_KEY: self._safe_repr(
                    self._RETURN_KEY, return_value
                )
            },
        )

    def event(self, name, cat, ph, args=None):
        self._trace.add_event(
            DurationTraceEvent(name=name, cat=cat, ph=ph, args=args,)
        )

    @classmethod
    def _fn_name(cls, fn):
        return f"{fn.__module__}.{fn.__qualname__}"

    @staticmethod
    def _fn_cat(fn):
        if not hasattr(fn, "__code__"):
            return "<unknown>"
        code = fn.__code__
        return f"{code.co_filename}:{code.co_firstlineno}"

    @classmethod
    def _fn_args(cls, fn, args, kwargs):
        bound_arguments = inspect.signature(fn).bind(*args, **kwargs)
        result = {}
        for key, val in bound_arguments.arguments.items():
            result[key] = cls._safe_repr(key, val)
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
            and frame.f_back.f_locals.get("_panopticon_marker")
            and frame.f_back.f_locals.get("_panopticon_marker").get_trace()
            == self.get_trace()
        )

    def _name(self, frame, event, arg):
        # Avoiding name cache
        return "... " + super()._get_frame_name(frame) + " ..."
