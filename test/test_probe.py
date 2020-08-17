import io
import unittest
import warnings
from test.utils import parse_json_trace

from panopticon.probe import probe
from panopticon.trace import StreamingTrace


class TestProbe(unittest.TestCase):
    def test_simple_probe(self):
        output = io.StringIO()
        trace = StreamingTrace(output)

        @probe(trace)
        def hello_world():
            print("Hello, world")

        hello_world()

        json_trace = parse_json_trace(output.getvalue())
        events = len(json_trace)

        self.assertTrue(events & 1 == 0)

        for i in range(events // 2):
            self.assertEquals(
                json_trace[i]["name"], json_trace[events - i - 1]["name"]
            )
            self.assertEquals(json_trace[i]["ph"], "B")
            self.assertEquals(json_trace[events - i - 1]["ph"], "E")

    def test_nested_probe(self):
        output = io.StringIO()
        trace = StreamingTrace(output)

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
            "test_probe.outer_hello",
            "test_probe.inner_hello",
            "test_probe.unprobed",
            "<<< test_probe.TestProbe.test_nested_probe >>>",
        ]
        for fn_name in check_functions:
            with self.subTest("{fn_name}", fn_name=fn_name):
                self.assertEqual(
                    sum(1 for x in json_trace if x["name"] == fn_name),
                    2,
                    msg=f"{fn_name}",
                )

    def test_nested_probe_warning(self):
        output1 = io.StringIO()
        trace1 = StreamingTrace(output1)

        output2 = io.StringIO()
        trace2 = StreamingTrace(output2)

        @probe(trace1)
        def inner_hello():
            print("world")

        @probe(trace2)
        def outer_hello():
            print("hello, ", end="")
            inner_hello()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            outer_hello()

            self.assertEqual(len(w), 1)
            assert issubclass(w[-1].category, RuntimeWarning)
            assert "Multiple" in str(w[-1].message)

        json_trace1 = parse_json_trace(output1.getvalue())
        self.assertEquals(json_trace1, [])
