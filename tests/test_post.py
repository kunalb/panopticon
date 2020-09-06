#!/bin/env/python3

import copy
import json
import tempfile
import unittest

from panopticon.post import (
    _CELL_PADDING,
    _CELL_WIDTH,
    _flatten_events,
    flatten,
)
from tests.utils import record


class TestFlatten(unittest.TestCase):
    def test_flatten_no_arguments_raises(self):
        with self.assertRaises(ValueError) as e:
            flatten()
        assert "Exactly one of" in str(e.exception)

    def test_flatten_multiple_arguments_raises(self):
        with self.assertRaises(ValueError) as e:
            flatten(trace_file="a_file", trace_str="a_string")
        assert "Exactly one of" in str(e.exception)

    def test_flatten_noop_file(self):
        self.assertEqual(flatten(trace_json=[]), [])

    def test_flatten_noop_str(self):
        self.assertEquals(flatten(trace_str="[]"), [])

    def test_flatten_noop_file(self):
        with tempfile.NamedTemporaryFile(mode="w") as test_file:
            test_file.write("[]")
            test_file.flush()

            self.assertEquals(flatten(trace_file=test_file.name), [])

    def test_flatten_single_event(self):
        trace = [
            {
                "name": "hello.<module>",
                "cat": "panopticon_traces/hello.py:3",
                "ph": "B",
                "args": None,
                "ts": 77888826106.828,
                "pid": 54341,
                "tid": 54341,
            },
            {
                "name": "hello.<module>",
                "cat": "panopticon_traces/hello.py:3",
                "ph": "E",
                "args": None,
                "ts": 77888826106.828,
                "pid": 54341,
                "tid": 54341,
            },
        ]

        flattened = record(_flatten_events(trace))
        self.assertEquals(trace[0]["ts"], 0)
        self.assertEquals(trace[1]["ts"], _CELL_WIDTH - _CELL_PADDING)

    def test_flatten_single_stack(self):
        flattened = record(_flatten_events(_sample_trace))

        for event in flattened:
            self.assertEquals(
                event["ts"],
                0 if event["ph"] == "B" else _CELL_WIDTH - _CELL_PADDING,
            )

    def test_flatten_multiple_threads_single_stack(self):
        multi_thread_trace = copy.deepcopy(_sample_trace) + copy.deepcopy(
            _sample_trace
        )
        for i in range(0, len(_sample_trace)):
            multi_thread_trace[i]["tid"] = 1337
        flattened = record(_flatten_events(multi_thread_trace))

        for event in flattened:
            self.assertEquals(
                event["ts"],
                0 if event["ph"] == "B" else _CELL_WIDTH - _CELL_PADDING,
            )

    def test_flatten_consecutive_stacks(self):
        consecutive_stacks = copy.deepcopy(_sample_trace) + copy.deepcopy(
            _sample_trace
        )
        for i in range(len(_sample_trace), len(consecutive_stacks)):
            consecutive_stacks[i]["ts"] += 1000
        record(consecutive_stacks)

        flattened = record(_flatten_events(consecutive_stacks))

        for event in flattened[: len(_sample_trace)]:
            self.assertEquals(
                event["ts"],
                0 if event["ph"] == "B" else _CELL_WIDTH - _CELL_PADDING,
            )
        for event in flattened[len(_sample_trace) :]:
            self.assertEquals(
                event["ts"],
                _CELL_WIDTH
                if event["ph"] == "B"
                else _CELL_WIDTH * 2 - _CELL_PADDING,
            )

    def test_flatten_complex_stack(self):
        record(_complex_stack)
        flattened = record(_flatten_events(_complex_stack))
        self.assertEqual(
            [x["ts"] for x in flattened],
            [
                0,
                0,
                _CELL_WIDTH - _CELL_PADDING,
                _CELL_WIDTH,
                2 * _CELL_WIDTH - _CELL_PADDING,
                2 * _CELL_WIDTH - _CELL_PADDING,
            ],
        )


_sample_trace = [
    {
        "name": "hello.<module>",
        "cat": "panopticon_traces/hello.py:3",
        "ph": "B",
        "args": None,
        "ts": 77888826106.828,
        "pid": 54341,
        "tid": 54341,
    },
    {
        "name": "hello.main",
        "cat": "panopticon_traces/hello.py:7",
        "ph": "B",
        "args": None,
        "ts": 77888826134.457,
        "pid": 54341,
        "tid": 54341,
    },
    {
        "name": "hello.test",
        "cat": "panopticon_traces/hello.py:3",
        "ph": "B",
        "args": None,
        "ts": 77888826162.517,
        "pid": 54341,
        "tid": 54341,
    },
    {
        "name": "<built-in function print>",
        "cat": "c function",
        "ph": "B",
        "args": None,
        "ts": 77888826214.098,
        "pid": 54341,
        "tid": 54341,
    },
    {
        "name": "<built-in function print>",
        "cat": "c function",
        "ph": "E",
        "args": None,
        "ts": 77888826258.341,
        "pid": 54341,
        "tid": 54341,
    },
    {
        "name": "hello.test",
        "cat": "panopticon_traces/hello.py:3",
        "ph": "E",
        "args": None,
        "ts": 77888826285.183,
        "pid": 54341,
        "tid": 54341,
    },
    {
        "name": "hello.main",
        "cat": "panopticon_traces/hello.py:7",
        "ph": "E",
        "args": None,
        "ts": 77888826326.289,
        "pid": 54341,
        "tid": 54341,
    },
    {
        "name": "hello.<module>",
        "cat": "panopticon_traces/hello.py:3",
        "ph": "E",
        "args": None,
        "ts": 77888826349.864,
        "pid": 54341,
        "tid": 54341,
    },
]

_complex_stack = [
    {
        "name": "A",
        "cat": "somefile.py",
        "ph": "B",
        "ts": 1000,
        "pid": 1,
        "tid": 1,
    },
    {
        "name": "B",
        "cat": "somefile.py",
        "ph": "B",
        "ts": 1100,
        "pid": 1,
        "tid": 1,
    },
    {"ph": "E", "ts": 1200, "pid": 1, "tid": 1,},
    {
        "name": "C",
        "cat": "somefile.py",
        "ph": "B",
        "ts": 1300,
        "pid": 1,
        "tid": 1,
    },
    {"ph": "E", "ts": 1400, "pid": 1, "tid": 1,},
    {"ph": "E", "ts": 1500, "pid": 1, "tid": 1,},
]
