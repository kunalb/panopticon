#!/bin/env python3

"""The actual tracer"""

import asyncio
import dis
import inspect
import opcode
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
        if self._skip(frame):
            return

        self._call(frame, event, arg)

    @staticmethod
    def _skip(frame):
        return isinstance(frame.f_locals.get('self'), Tracer)

    def _call(self, frame, event, arg):
        raise codeNotImplementedError()
    

class FunctionTracer(Tracer):

    def __init__(self):
        super().__init__()
        self._state = threading.local()
        self._state.active = None

    def _call(self, frame, event, arg):
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
    def _name(code):
        name = os.path.splitext(os.path.basename(code.co_filename))[0]
        return f"{name}.{code.co_name}"

_CODE_FLAGS = {}
for flag, name in dis.COMPILER_FLAG_NAMES.items():
    _CODE_FLAGS[name] = flag

class AsyncioTracer(FunctionTracer):

    CONTINUABLE_CODE_TYPES = [
        "GENERATOR",
        "ASYNC_GENERATOR",
        "COROUTINE",
        "ITERABLE_COROUTINE",
    ]

    CONTINUABLE_CODE_FLAGS = 0
    for flag in CONTINUABLE_CODE_TYPES:
        CONTINUABLE_CODE_FLAGS |= _CODE_FLAGS[flag]

    def __init__(self):
        super().__init__()
        self._ids = set({})

    def _call(self, frame, event, arg):
        code = frame.f_code
        frame_id = id(frame)

        if event == "return" and self._is_continuable_code(code):
            if self._is_frame_finished(frame, arg):
                self._ids.discard(frame_id)
            else:
                self._ids.add(frame_id)
                self._trace.add_event(FlowTraceEvent(
                    name=code.co_name,
                    cat=self._code_category(code),
                    ph=Phase.Flow.START,
                    bp=FlowBindingPoint.ENCLOSING,
                    id=frame_id,
                ))

        super()._call(frame, event, arg)

        # Emit the end point after starting the run
        if id(frame) in self._ids and event == "call":
            self._trace.add_event(FlowTraceEvent(
                name=code.co_name,
                cat=self._code_category(code),
                ph=Phase.Flow.END,
                bp=FlowBindingPoint.ENCLOSING,
                id=id(frame),
            ))

    @staticmethod
    def _is_frame_finished(frame, arg):
        code = frame.f_code
        offset = frame.f_lasti
        return opcode.opname[code.co_code[offset]] == "RETURN_VALUE"

    @classmethod
    def _is_continuable_code(cls, code):
        return code.co_flags & cls.CONTINUABLE_CODE_FLAGS > 0

    @classmethod
    def _code_category(cls, code):
        for flag in cls.CONTINUABLE_CODE_TYPES:
            if _CODE_FLAGS[flag] & code.co_flags > 0:
                return flag
        return "UNKNOWN"
