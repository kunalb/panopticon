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
    

class AsyncioTracer(Tracer):
    ...


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
                name=f"{code.co_name}",
                cat=f"{code.co_filename}",
                ph=ph,
            ))
        elif event == 'line':
            self._trace.add_event(InstantTraceEvent(
                name=f"{code.co_name}:{frame.f_lineno}",
                cat=f"{code.co_filename}",
            ))
        # else:
        #   print(frame, event, arg)
        
        return self
