#!/bin/env/python3

"""Utilities for post-processing traces for legibility"""

import json
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Union

from .trace import Phase

logger = logging.getLogger(__name__)

_CELL_WIDTH = 100
_CELL_PADDING = 10

_EVENTS_KEY = "traceEvents"


def flatten(
    *,
    trace_file: Optional[str] = None,
    trace_str: Optional[str] = None,
    trace_json: Optional[Union[Dict, List]] = None,
) -> Union[List, Dict]:
    """
    Destroys all the timing information in a trace to make all columns
    equally sized and minimize empty space. This is useful when the
    valuable part of the trace is understanding the code execution
    and not paying attention to timing information whatsoever.

    (Note that the timing information is distorted and misleading
    because of the overhead from panopticon anyways.)

    The trace can be provided as any of a file, raw string, or
    parsed json blob.
    """

    _validate_highlander(trace_file, trace_str, trace_json)

    if trace_file:
        with open(trace_file) as infile:
            trace_str = infile.read()

    if trace_str:
        try:
            trace_json = json.loads(trace_str)
        except json.JSONDecodeError:
            trace_json = json.loads(trace_str.rstrip().rstrip(",") + "]")

    if isinstance(trace_json, list):
        trace_json = _flatten_events(trace_json)
    else:
        trace_json[_EVENTS_KEY] = _flatten_events(trace_json[_EVENTS_KEY])

    return trace_json


def _flatten_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Walks over the events maintaining per-thread stacks and an offset
    that keeps moving forward to allow for a minimum width.
    """

    stacks = defaultdict(list)
    offsets = defaultdict(lambda: 0)

    for i, event in enumerate(events):
        tid = event["tid"]

        if event["ph"] == Phase.Duration.START:
            events[i]["ts"] = offsets[tid]
            stacks[tid].append(i)

        elif event["ph"] == Phase.Duration.END:
            if not stacks[tid]:
                logger.warn(f"Discarding {event}")
                continue
            top = events[stacks[tid].pop()]

            if offsets[tid] == top["ts"]:
                offsets[tid] += _CELL_WIDTH
            events[i]["ts"] = offsets[tid] - _CELL_PADDING

    return events


def _validate_highlander(*args):
    values = sum(1 for x in args if x is not None)
    if values != 1:
        raise ValueError(f"Exactly one of {args} must be specified")
