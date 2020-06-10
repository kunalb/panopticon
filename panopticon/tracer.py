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
        sys.settrace(self)
        threading.settrace(self)
        return self

    def stop(self):
        sys.settrace(None)
        threading.settrace(None)

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
        code = frame.f_code

        if event == 'call' or event == 'return':
            ph = Phase.Duration.START if event == 'call' else Phase.Duration.END
            self._trace.add_event(DurationTraceEvent(
                name=f"{self._name(code)}",
                cat=f"{code.co_filename}",
                ph=ph,
            ))
        return self

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

        

        return self
            

