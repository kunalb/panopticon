#!/bin/env python3

import sys 

from .tracer import FunctionTracer

def custom_print():
    print(f"Hello, World")

def main():
    with FunctionTracer() as ft:
        custom_print()

    print(ft.get_trace(), file=sys.stderr)

if __name__ == "__main__":
    main()
