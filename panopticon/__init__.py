#!/bin/env python3

import sys

from dataclasses import dataclass
from typing import Any, Dict

from .tracer import AsyncioTracer

def start() -> AsyncioTracer:
    ...

def stop() -> None:
    ...

