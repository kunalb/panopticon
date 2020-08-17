#!/bin/env python3

import inspect
import unittest
from unittest.mock import Mock

from panopticon.tracer import FunctionTracer


class TestTracer(unittest.TestCase):
    def test_method_name(self):
        self.assertEqual(
            FunctionTracer._name(inspect.currentframe()),
            "test_tracer.TestTracer.test_method_name",
        )

    def test_function_name(self):
        def test_fn():
            self.assertEqual(
                FunctionTracer._name(inspect.currentframe()),
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
            FunctionTracer._name(mock_frame), "package.__init__.some_fn"
        )
