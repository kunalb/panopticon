import io
import unittest
from test.utils import parse_json_trace

from panopticon.probe import probe


class TestProbe(unittest.TestCase):
    def test_simple_probe(self):
        output = io.StringIO()

        @probe(file=output)
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
