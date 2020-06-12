#!/bin/env python3

"""The actual tracer"""

import os
import sys
import threading

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
        raise NotImplementedError()
    

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
        self._ids = {}

    def __call__(self, frame, event, arg):
        code = frame.f_code

        # Emit the flow event before closing it out 
        if (code.co_filename.endswith("asyncio/base_events.py") and
            code.co_name == "create_task" and
            event == "return"):
            flow_id = len(self._ids)
            frame = arg.get_coro().cr_frame
            task_name = arg.get_name()
            self._ids[id(frame)] = (task_name, flow_id)
            self._trace.add_event(FlowTraceEvent(
                name=task_name,
                cat="async task",
                ph=Phase.Flow.START,
                id=flow_id
            ))
        elif id(frame) in self._ids and event == "return":
            details = self._ids[id(frame)]
            # optimistically add another line
            self._trace.add_event(FlowTraceEvent(
                name=details[0],
                cat="async task",
                ph=Phase.Flow.START,
                bp=FlowBindingPoint.ENCLOSING,
                id=details[1],
            ))

        super().__call__(frame, event, arg)

        # Emit the end point after starting the run
        if id(frame) in self._ids and event == "call":
            details = self._ids[id(frame)]
            self._trace.add_event(FlowTraceEvent(
                name=details[0],
                cat="async task",
                ph=Phase.Flow.END,
                bp=FlowBindingPoint.ENCLOSING,
                id=details[1],
            ))
