#!/bin/env python3

"""The actual tracer"""

import asyncio
import dis
import inspect
import os
import sys
import threading
import weakref

from .trace import *


class Tracer:

    def __init__(self):
        self._trace = Trace()

    def start(self):
        threading.setprofile(self) # Avoid noise
        sys.setprofile(self)
        return self

    def stop(self):
        sys.setprofile(None)
        threading.setprofile(None)

    def get_trace(self):
        return self._trace

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def __call__(self, frame, event, arg):
        raise codeNotImplementedError()
    

class FunctionTracer(Tracer):

    def __init__(self):
        super().__init__()
        self._state = threading.local()
        self._state.active = None

    def __call__(self, frame, event, arg):
        if self._skip(frame):
            return

        code = frame.f_code

        if event == 'call' or event == 'c_call':
            ph = Phase.Duration.START
        elif event == 'return' or event == 'c_return':
            ph = Phase.Duration.END
        else:
            ph = None

        if event == 'c_call' or event == 'c_return':
            name = str(arg)
            cat = 'c function'
        elif event == 'call' or event == 'return':
            name = self._name(code)
            cat = code.co_filename
        else:
            name = None
            cat = None

        if ph:
            self._trace.add_event(DurationTraceEvent(
                name=name,
                cat=cat,
                ph=ph,
            ))

    @staticmethod
    def _skip(frame):
        # TODO Move this into Tracer
        return isinstance(frame.f_locals.get('self'), Tracer)

    @staticmethod
    def _name(code):
        name = os.path.splitext(os.path.basename(code.co_filename))[0]
        return f"{name}.{code.co_name}"


class AsyncioTracer(FunctionTracer):

    def __init__(self):
        super().__init__()
        self._ids = set({})

    def __call__(self, frame, event, arg):
        code = frame.f_code
        frame_id = id(frame)

        if event == "return" and self._is_coroutine_function(frame):
            if self._is_coroutine_finished(arg):
                self._ids.discard(frame_id)
            else:
                self._ids.add(frame_id)
                self._trace.add_event(FlowTraceEvent(
                    name=code.co_name,
                    cat="Coroutine",
                    ph=Phase.Flow.START,
                    bp=FlowBindingPoint.ENCLOSING,
                    id=frame_id,
                ))

        super().__call__(frame, event, arg)

        # Emit the end point after starting the run
        if id(frame) in self._ids and event == "call":
            self._trace.add_event(FlowTraceEvent(
                name=code.co_name,
                cat="Coroutine",
                ph=Phase.Flow.END,
                bp=FlowBindingPoint.ENCLOSING,
                id=id(frame),
            ))

    @staticmethod
    def _is_coroutine_finished(arg):
        return not isinstance(arg, asyncio.Future)

    @staticmethod
    def _is_coroutine_function(frame):
        coroutine_flag = 128
        code = frame.f_code
        return code.co_flags & coroutine_flag > 0
