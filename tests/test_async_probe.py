#!/bin/env python3

import asyncio
import io
import sys
import unittest

from panopticon.probe import probe
from panopticon.trace import StreamingTrace
from panopticon.tracer import FunctionTracer
from tests.utils import parse_json_trace, record

if sys.version_info >= (3, 8):

    class TestAsyncProbe(unittest.IsolatedAsyncioTestCase):
        async def test_probe_async_function(self):
            output = io.StringIO()
            trace = record(StreamingTrace(output))

            @probe(trace)
            async def test_function(alpha):
                print("Step 1")
                await asyncio.sleep(0.0001)
                print("Step 2")
                await asyncio.sleep(0.0001)
                print("Step 3")
                return alpha * alpha

            await test_function(2)
            json_trace = parse_json_trace(output.getvalue())

            name = (
                "TestAsyncProbe.test_probe_async_function"
                ".<locals>.test_function"
            )
            coroutine_traces = [x for x in json_trace if x["name"] == name]

            self.assertEquals(len(coroutine_traces), 8)
            self.assertEquals(coroutine_traces[0]["args"]["alpha"], repr(2))
            self.assertEquals(
                coroutine_traces[-1]["args"][FunctionTracer._RETURN_KEY],
                repr(4),
            )

        async def test_nested_async_functions(self):
            output = io.StringIO()
            trace = record(StreamingTrace(output))

            @probe(trace)
            async def outer():
                return await unprobed()

            async def unprobed():
                return await inner()

            @probe(trace)
            async def inner():
                return 1

            await outer()

            json_trace = parse_json_trace(output.getvalue())
            name = "... nose2.<module> ..."
            self.assertEquals(
                sum(1 for x in json_trace if x["name"] == name), 4
            )
