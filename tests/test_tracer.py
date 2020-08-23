#!/bin/env python3

import inspect
import unittest
from unittest.mock import Mock

from panopticon.tracer import FunctionTracer
from tests.utils import parse_json_trace, record


class TestTracer(unittest.TestCase):
    def test_argument_capture(self):
        with FunctionTracer(capture_args=lambda _1, _2, _3: True) as ft:
            some_function()

        json_trace = parse_json_trace(str(record(ft.get_trace())))

        self.assertEquals(
            json_trace["traceEvents"][1]["args"]["x"], "2",
        )
        self.assertEquals(
            json_trace["traceEvents"][2]["args"][FunctionTracer._RETURN_KEY],
            "4",
        )

    def test_method_name(self):
        self.assertEqual(
            FunctionTracer._get_frame_name(inspect.currentframe()),
            "test_tracer.TestTracer.test_method_name",
        )

    def test_function_name(self):
        def test_fn():
            self.assertEqual(
                FunctionTracer._get_frame_name(inspect.currentframe()),
                "test_tracer.test_fn",
            )

        test_fn()

    def test_name_module_heuristics(self):
        """Overly mocked, but I can't think of an easier fix"""
        mock_frame = Mock()
        mock_frame.f_locals = {}
        mock_frame.f_code = Mock()
        mock_frame.f_code.co_name = "some_fn"
        mock_frame.f_code.co_filename = "a/b/c/package/__init__.py"

        self.assertEqual(
            FunctionTracer._get_frame_name(mock_frame),
            "package.__init__.some_fn",
        )


def some_function():
    inner_function(2)


def inner_function(x):
    return x * x
