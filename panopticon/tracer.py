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
    """TODO Fix the file names being shown, this isn't very useful"""

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
        elif event == 'line':
            self._trace.add_event(InstantTraceEvent(
                name=f"{code.co_name}:{frame.f_lineno}",
                cat=f"{code.co_filename}",
            ))

        # TODO Figure out how to print native calls here
        # else:
        #   print(frame, event, arg)
        
        return self

    @staticmethod
    def _name(code):
        name = os.path.splitext(os.path.basename(code.co_filename))[0]
        return f"{name}.{code.co_name}"


class AsyncioTracer(FunctionTracer):
    """
    TODO Add support for intercepting Task creation and Handle running
    """
    ...

