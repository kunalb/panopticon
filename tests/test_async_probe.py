#!/bin/env python3

import asyncio
import io
import sys
import unittest

from panopticon.probe import probe
from panopticon.trace import StreamingTrace
from tests.utils import parse_json_trace, record


@unittest.skipUnless(
    sys.version_info >= (3, 8), "Async test requires Python 3.8+"
)
class TestAsyncProbe(unittest.IsolatedAsyncioTestCase):
    async def test_probe_async_function(self):
        output = io.StringIO()
        trace = record(StreamingTrace(output))

        @probe(trace)
        async def test_function():
            print("Step 1")
            await asyncio.sleep(0.0001)
            print("Step 2")
            await asyncio.sleep(0.0001)
            print("Step 3")
            return 4

        await test_function()
        json_trace = parse_json_trace(output.getvalue())
