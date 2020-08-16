#!/bin/env python3

"""Test the external API defined in __init__.py"""

import json
import tempfile
import unittest

from panopticon import trace


class TestInit(unittest.TestCase):
    def test_simple_trace(self):
        with tempfile.NamedTemporaryFile(mode="w+") as outfile:
            with trace(outfile.name):
                print("Hello")
            trace_contents = outfile.read()

        # Add trailing ] to make it valid json
        trace_json = _parse_json_trace(trace_contents)

        tests = {"name": "<built-in function print>", "cat": "c function"}

        for key, expected in tests.items():
            for i in [1, 2]:
                self.assertEquals(trace_json[i][key], expected)

        self.assertEquals(trace_json[1]["ph"], "B")
        self.assertEquals(trace_json[2]["ph"], "E")


def _parse_json_trace(text):
    if not text.endswith("]"):
        text = text.rstrip().rstrip(",") + "\n]"

    return json.loads(text)