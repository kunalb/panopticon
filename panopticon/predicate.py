#!/bin/env/python3

"""
Predicates that can be used for choosing which frames to trace
or capture arguments from.
"""

import os
import sys
import types
from typing import Any, Callable, Optional

Predicate = Callable[[types.FrameType, str, Optional[Any]], bool]


# Sugar


def module_equals(m: str):
    """Guesses the module name and does an exact match. See also file"""
    return file(lambda f: extract_module(f) == m)


def stdlib():
    """Match any code defined in the stdlib"""
    prefix = sys.base_prefix
    python_path = (
        f"{prefix}/lib/python{sys.version_info.major}.{sys.version_info.minor}"
    )
    return file(lambda f: f.startswith(python_path))


def native():
    """Match C functions"""
    return lambda frame, event, arg: event == "c_call" or event == "c_return"


# Extractors


def file(f: Callable[[str], bool]):
    def filter_file(
        frame: types.FrameType, event: str, arg: Optional[Any]
    ) -> bool:
        return f(frame.f_code.co_filename)

    return filter_file


# Combinators


def not_(f: Predicate) -> bool:
    return lambda *args, **kwargs: not f(*args, **kwargs)


def or_(f1: Predicate, f2: Predicate) -> bool:
    return lambda *args, **kwargs: f1(*args, **kwargs) or f2(*args, **kwargs)


def and_(f1: Predicate, f2: Predicate) -> bool:
    return lambda *args, **kwargs: f1(*args, **kwargs) and f2(*args, **kwargs)


# Utilities


def extract_module(path: str) -> str:
    package_path, module = os.path.split(path)
    return os.path.basename(package_path)
