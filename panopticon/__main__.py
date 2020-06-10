#!/bin/env python3

import asyncio
import sys 

from .tracer import AsyncioTracer

async def sleepy_hello():
    for x in range(4):
        await asyncio.sleep(.01)
        print(f"Hello,", end=" ")
    print("World")

def main():
    with AsyncioTracer() as at:
        asyncio.run(sleepy_hello())

    print(at.get_trace(), file=sys.stderr)

if __name__ == "__main__":
    main()
