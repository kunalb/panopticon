#!/bin/env python3

import asyncio
import sys 

from .tracer import AsyncioTracer

async def sleepy_generator():
    for x in range(1):
        await asyncio.sleep(.01)
        yield x

async def gen_consumer():
    async for x in sleepy_generator():
        print(f"Hello,", end=" ")

    async for x in sleepy_generator():
        print(f"Hello,", end=" ")

    print("World")

def main():
    with AsyncioTracer() as at:
        asyncio.run(gen_consumer())

    print(at.get_trace(), file=sys.stderr)

if __name__ == "__main__":
    main()
