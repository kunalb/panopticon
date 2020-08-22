#!/bin/env python3

"""Utility functions to help with testing"""


import atexit
import glob
import inspect
import json
import os
import unittest
from pathlib import Path
from typing import TypeVar, Union

from panopticon.trace import Trace

_RECORDED_TRACES = set()

T = TypeVar("T", Trace, str)


def record(trace: T) -> T:
    """Saves traces from the tests for debugging under test/traces.

    These can be very useful for debugging and working with tests."""

    output_dir = Path(__file__).parent / "traces"
    output_dir.mkdir(exist_ok=True)

    test_frame = inspect.currentframe().f_back
    test_name = test_frame.f_code.co_name
    test_case = type(test_frame.f_locals["self"]).__name__
    line_no = test_frame.f_lineno

    trace_name = f"{test_case}_{test_name}"

    if not trace_name in _RECORDED_TRACES:
        _RECORDED_TRACES.add(trace_name)
        for t in glob.glob(str(output_dir / trace_name) + "*.trace"):
            os.remove(t)

    trace_name = f"{trace_name}_{line_no}.trace"

    def save_trace():
        with open(output_dir / trace_name, "w") as out:
            out.write(str(trace))

    atexit.register(save_trace)

    return trace


def parse_json_trace(text):
    try:
        return json.loads(text)
    except:
        return json.loads(text.rstrip().rstrip(",") + "\n]")
