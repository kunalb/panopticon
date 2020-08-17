#!/bin/env python3

"""Utility functions to help with testing"""


import json


def parse_json_trace(text):
    if not text.endswith("]"):
        text = text.rstrip().rstrip(",") + "\n]"

    return json.loads(text)
