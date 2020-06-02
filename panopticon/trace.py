#!/bin/env python3

"""Classes to generate a tracefile in the right format"""

from __future__ import annotations

import json

from typing import Dict
from dataclasses import asdict, dataclass, field
from time import perf_counter_ns

class Trace:

    def __init__(self):
        self._events = []

    def add_event(self, event: TraceEvent):
        self._events.append(event)

    def __str__(self) -> str:
        return json.dumps({
            "traceEvents": [asdict(x) for x in self._events],
            "displayTimeUnit": "ns",
            "otherData": {
                "version": "Panopticon 0.1"
            },
        })
        

@dataclass
class TraceEvent:
    name: str
    cat: str
    ph: str
    pid: int
    tid: int
    args: Optional[Dict[str, Any]] = None
    ts: int = field(init=False)

    def __post_init__(self):
        self.ts = perf_counter_ns()

@dataclass
class DurationTraceEvent(TraceEvent):
    ...
