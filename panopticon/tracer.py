#!/bin/env python3

"""The actual tracer"""

import abc
import dis
import os
import sys
import threading
from typing import Any, Dict, Optional

import opcode

from .trace import (
    DurationTraceEvent,
    FlowBindingPoint,
    FlowTraceEvent,
    Phase,
    Trace,
)


class Tracer(abc.ABC):
    def __init__(self, trace=None):
        self._trace = trace or Trace()

    def start(self):
        threading.setprofile(self)  # Avoid noise
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
        """Skip anything belonging to the Panopticon module.

        TODO: Also skip any children triggered from here."""
        path = frame.f_code.co_filename
        package_path, module = os.path.split(path)
        package = os.path.basename(package_path)
        return package == "panopticon"

    @abc.abstractmethod
    def _call(self, frame, event, arg):
        ...


class FunctionTracer(Tracer):
    _RETURN_KEY = "[return value]"

    def __init__(self, trace=None, capture_args=None):
        super().__init__(trace)
        self._state = threading.local()
        self._state.active = None
        self._capture_args = capture_args

    def _call(self, frame, event, arg):
        code = frame.f_code

        if event == "call" or event == "c_call":
            ph = Phase.Duration.START
        elif event == "return" or event == "c_return":
            ph = Phase.Duration.END
        else:
            ph = None

        if event == "c_call" or event == "c_return":
            name = str(arg)
            cat = "c function"
        elif event == "call" or event == "return":
            name = self._name(frame)
            cat = f"{code.co_filename}:{code.co_firstlineno}"
        else:
            name = None
            cat = None

        if ph:
            self._trace.add_event(
                DurationTraceEvent(
                    name=name,
                    cat=cat,
                    ph=ph,
                    args=self._capture_arguments(frame, event, arg),
                )
            )

    def _capture_arguments(
        self, frame, event, arg
    ) -> Optional[Dict[str, Any]]:
        if not self._capture_args or not self._capture_args(frame, event, arg):
            return None

        if event == "call":
            return {key: repr(val) for key, val in frame.f_locals.items()}

        if event == "return":
            return {self._RETURN_KEY: repr(arg)}

        return None

    @classmethod
    def _name(cls, frame):
        code = frame.f_code

        classname = cls._get_class_name(frame)
        classname = "." + classname if classname else ""

        module = cls._get_module_name(frame)

        return f"{module}{classname}.{code.co_name}"

    @classmethod
    def _get_class_name(cls, frame) -> Optional[str]:
        """Heuristics to extract classname for a method"""
        code_name = frame.f_code.co_name
        local_self = frame.f_locals.get("self")
        # print(local_self)

        if (
            local_self is not None
            and hasattr(local_self, code_name)
            and callable(getattr(local_self, code_name))
        ):
            return type(local_self).__name__
        return None

    @classmethod
    def _get_module_name(cls, frame) -> str:
        """Some heuristics to get useful names for modules"""
        code = frame.f_code
        filename = code.co_filename

        module, _ = os.path.splitext(os.path.basename(filename))

        if module == "__init__" or module == "__main__":
            module = (
                os.path.basename(os.path.split(filename)[0]) + "." + module
            )

        return module


_CODE_FLAGS = {}
for flag, name in dis.COMPILER_FLAG_NAMES.items():
    _CODE_FLAGS[name] = flag


class AsyncioTracer(FunctionTracer):

    RETURN_OPCODE = opcode.opmap["RETURN_VALUE"]  # 83

    CONTINUABLE_CODE_TYPES = [
        "GENERATOR",
        "ASYNC_GENERATOR",
        "COROUTINE",
        "ITERABLE_COROUTINE",
    ]

    CONTINUABLE_CODE_FLAGS = 0
    for flag in CONTINUABLE_CODE_TYPES:
        CONTINUABLE_CODE_FLAGS |= _CODE_FLAGS[flag]

    def __init__(self, trace=None, capture_args=None):
        super().__init__(trace, capture_args)
        self._ids = set()

    def _call(self, frame, event, arg):
        code = frame.f_code
        frame_id = id(frame)

        if event == "return" and self._is_continuable_code(code):
            if self._is_frame_finished(frame, arg):
                self._ids.discard(frame_id)
            else:
                self._ids.add(frame_id)
                self._trace.add_event(
                    FlowTraceEvent(
                        name=code.co_name,
                        cat=self._code_category(code),
                        ph=Phase.Flow.START,
                        bp=FlowBindingPoint.ENCLOSING,
                        id=frame_id,
                    )
                )

        super()._call(frame, event, arg)

        # Emit the end point after starting the run
        if id(frame) in self._ids and event == "call":
            self._trace.add_event(
                FlowTraceEvent(
                    name=code.co_name,
                    cat=self._code_category(code),
                    ph=Phase.Flow.END,
                    bp=FlowBindingPoint.ENCLOSING,
                    id=id(frame),
                )
            )

    @classmethod
    def _is_frame_finished(cls, frame, arg):
        code = frame.f_code
        offset = frame.f_lasti
        return code.co_code[offset] == cls.RETURN_OPCODE

    @classmethod
    def _is_continuable_code(cls, code):
        return code.co_flags & cls.CONTINUABLE_CODE_FLAGS > 0

    @classmethod
    def _code_category(cls, code):
        for flag in cls.CONTINUABLE_CODE_TYPES:
            if _CODE_FLAGS[flag] & code.co_flags > 0:
                return flag
        return "UNKNOWN"
