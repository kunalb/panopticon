#!/bin/env python3

"""Classes to generate a tracefile in the right format"""

from __future__ import annotations

import io
import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from panopticon.version import version


class Trace:
    def __init__(self):
        self._events = []

    def add_event(self, event: TraceEvent):
        self._events.append(event)

    def __str__(self) -> str:
        return json.dumps(
            {
                "traceEvents": [asdict(x) for x in self._events],
                "displayTimeUnit": "ns",
                "otherData": {"version": f"Panopticon {version}"},
            },
            indent="  ",
        )


class StreamingTrace(Trace):
    """Streams data to a file without keeping it in memory"""

    def __init__(self, stream: io.IOBase):
        self._out = stream
        self._out.write("[\n")  # Opening brace
        self._out.flush()

    def add_event(self, event: TraceEvent):
        json.dump(asdict(event), self._out)
        self._out.write(",\n")
        self._out.flush()

    def __str__(self) -> str:
        if hasattr(self._out, "getvalue") and callable(
            getattr(self._out, "getvalue")
        ):
            return self._out.getvalue()
        else:
            return f"StreamingTrace ({self._out})"


class _SerializableEnum(str, Enum):
    ...


class Phase:
    class Duration(_SerializableEnum):
        START = "B"
        END = "E"

    class Instant(_SerializableEnum):
        INSTANT = "i"

    class Counter(_SerializableEnum):
        COUNTER = "c"

    class Complete(_SerializableEnum):
        INSTANT = "X"

    class Async(_SerializableEnum):
        START = "b"
        INSTANT = "n"
        END = "e"

    class Flow(_SerializableEnum):
        START = "s"
        INSTANT = "t"
        END = "f"

    class Object(_SerializableEnum):
        NEW = "N"
        SNAPSHOT = "O"
        DESTROY = "D"


@dataclass
class TraceEvent:
    name: str
    cat: str
    ph: str
    args: Optional[Dict[str, Any]] = None
    ts: int = field(init=False)
    tts: int = field(init=False)
    pid: int = field(init=False)
    tid: int = field(init=False)

    def __post_init__(self):
        # Allow aligning with other traces
        self.ts = time.time_ns() / 1000
        self.tts = time.thread_time_ns() / 1000
        self.pid = os.getpid()
        self.tid = _get_thread_id()


@dataclass
class DurationTraceEvent(TraceEvent):
    ph: Phase.Duration


class InstantScope(_SerializableEnum):
    GLOBAL = "g"
    PROCESS = "p"
    THREAD = "t"


@dataclass
class InstantTraceEvent(TraceEvent):

    ph: Phase.Instant = Phase.Instant.INSTANT
    s: InstantScope = InstantScope.THREAD


class FlowBindingPoint(_SerializableEnum):
    ENCLOSING = "e"
    NEXT = "n"


@dataclass
class FlowTraceEvent(TraceEvent):
    id: int = 0  # ick
    ph: Phase.Flow = Phase.Flow.START
    bp: FlowBindingPoint = FlowBindingPoint.ENCLOSING


def _get_thread_id() -> int:
    try:
        return threading.get_native_id()
    except AttributeError:
        return threading.get_ident()
