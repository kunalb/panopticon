#!/bin/env python3

import argparse
import asyncio
import runpy
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
    parser = argparse.ArgumentParser(
        prog='panopticon',
        description="Generate async-aware traces from python code.")

    parser.add_argument('-o', '--output')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-m', '--module', help='Run module')
    group.add_argument('-c', '--command',
                        help='Run python statements as command')
    group.add_argument('path', nargs='?')
    args = parser.parse_args()


    if args.module:
        with AsyncioTracer() as at:
            runpy.run_module(args.module)
    elif args.command:
        with AsyncioTracer() as at:
            eval(args.command)
    elif args.path:
        with AsyncioTracer() as at:
            runpy.run_path(args.path)

    trace = at.get_trace()
    if args.output:
        with open(args.output, "w") as output_file:
            output_file.write(str(trace))
    else:
        print(str(trace), file=sys.stderr)


if __name__ == "__main__":
    main()
