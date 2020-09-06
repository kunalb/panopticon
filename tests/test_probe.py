import io
import unittest
import warnings
from unittest.mock import Mock

from panopticon.probe import probe
from panopticon.trace import StreamingTrace
from panopticon.tracer import FunctionTracer
from tests.utils import parse_json_trace, record


class TestProbe(unittest.TestCase):
    def test_simple_probe(self):
        output = io.StringIO()
        trace = record(StreamingTrace(output))

        @probe(trace)
        def hello_world():
            print("Hello, world")

        hello_world()

        json_trace = parse_json_trace(output.getvalue())
        events = len(json_trace)

        self.assertTrue(events & 1 == 0)

        for i in range(events // 2):
            self.assertEqual(
                json_trace[i]["name"], json_trace[events - i - 1]["name"]
            )
            self.assertEquals(json_trace[i]["ph"], "B")
            self.assertEquals(json_trace[events - i - 1]["ph"], "E")

    def test_args_and_return(self):
        output = io.StringIO()
        trace = record(StreamingTrace(output))

        @probe(trace)
        def strange(x, y, _z):
            return x * y

        strange(2, 3, "quirk")

        json_trace = parse_json_trace(output.getvalue())
        probe_events = [
            x for x in json_trace if not x["name"].startswith("...")
        ]

        self.assertEquals(probe_events[0]["args"]["x"], "2")
        self.assertEquals(probe_events[0]["args"]["y"], "3")
        self.assertEquals(probe_events[0]["args"]["_z"], "'quirk'")
        self.assertEquals(
            probe_events[1]["args"][FunctionTracer._RETURN_KEY], "6"
        )

    def test_nested_probe(self):
        output = io.StringIO()
        trace = record(StreamingTrace(output))

        @probe(trace)
        def inner_hello():
            print("world")

        def unprobed():
            inner_hello()

        @probe(trace)
        def outer_hello():
            print("hello, ", end="")
            unprobed()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            outer_hello()

            assert len(w) == 0

        json_trace = parse_json_trace(output.getvalue())

        check_functions = [
            (
                "tests.test_probe.TestProbe."
                "test_nested_probe.<locals>.outer_hello"
            ),
            (
                "tests.test_probe.TestProbe."
                "test_nested_probe.<locals>.inner_hello"
            ),
            "... test_probe.unprobed ...",
            "... test_probe.TestProbe.test_nested_probe ...",
        ]
        for fn_name in check_functions:
            self.assertEqual(
                sum(1 for x in json_trace if x["name"] == fn_name),
                2,
                msg=f"{fn_name}",
            )

    def test_probe_class(self):
        output = io.StringIO()
        trace = record(StreamingTrace(output))

        @probe(trace)
        class Test:
            def __init__(self):
                print("init")

            def foo(self):
                print("hello")

            def bar(self):
                print("world")

        test = Test()
        test.foo()
        test.bar()

        json_trace = parse_json_trace(output.getvalue())

        check_functions = [
            "tests.test_probe.TestProbe.test_probe_class.<locals>.Test.__init__",
            "tests.test_probe.TestProbe.test_probe_class.<locals>.Test.foo",
            "tests.test_probe.TestProbe.test_probe_class.<locals>.Test.bar",
        ]
        for fn_name in check_functions:
            self.assertEqual(
                sum(1 for x in json_trace if x["name"] == fn_name),
                2,
                msg=f"{fn_name}",
            )

    def test_wrap_behavior(self):
        @probe(Mock())
        def test_fn():
            """This is a docstring"""
            ...

        self.assertEquals(test_fn.__doc__, "This is a docstring")

    def test_generator(self):
        output = io.StringIO()
        trace = record(StreamingTrace(output))

        @probe(trace)
        def custom_gen(k):
            for x in range(5):
                yield x + k

        self.assertEqual(list(custom_gen(1)), list(range(1, 6)))

        json_trace = parse_json_trace(output.getvalue())
        name = (
            "tests.test_probe." "TestProbe.test_generator.<locals>.custom_gen"
        )

        gen_events = [x for x in json_trace if x["name"] == name]
        self.assertEqual(len(gen_events), 14)
        self.assertEqual(gen_events[0]["args"]["k"], "1")

        for x in range(1, 6):
            self.assertEqual(
                gen_events[x * 2 + 1]["args"][FunctionTracer._RETURN_KEY],
                repr(x),
            )

    def test_nested_generator(self):
        output = io.StringIO()
        trace = record(StreamingTrace(output))

        @probe(trace)
        def outer_gen():
            for y in inner_gen():
                yield y * y

        @probe(trace)
        def inner_gen():
            for x in range(5):
                yield x

        _results = list(outer_gen())

        json_trace = parse_json_trace(output.getvalue())
        name = "... nose2.<module> ..."
        self.assertEqual(sum(1 for x in json_trace if x["name"] == name), 14)
