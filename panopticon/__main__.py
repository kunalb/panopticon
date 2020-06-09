#!/bin/env python3

import asyncio
import sys 

from .tracer import FunctionTracer

async def sleepy_hello():
    await asyncio.sleep(.01)
    print(f"Hello, World")

def main():
    with FunctionTracer() as ft:
        asyncio.run(sleepy_hello())

    print(ft.get_trace(), file=sys.stderr)

if __name__ == "__main__":
    main()
