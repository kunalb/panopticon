#!/bin/env python3

import argparse
import asyncio
import runpy
import sys
import os

from .tracer import AsyncioTracer


def main():
    parser = argparse.ArgumentParser(
        prog="panopticon",
        description="Generate async-aware traces from python code.",
    )

    parser.add_argument("-o", "--output")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-c", "--command", help="Run python statements as command"
    )
    group.add_argument("path", nargs="?")

    parser.add_argument(
        "arguments",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the program",
    )
    args = parser.parse_args()

    # Adapted from trace.py
    if args.command:
        with AsyncioTracer() as at:
            eval(args.command)
    elif args.path:
        sys.argv = [args.path, *args.arguments]
        sys.path[0] = os.path.dirname(args.path)

        with open(args.path) as program:
            code = compile(
                program.read(), args.path, "exec", dont_inherit=True
            )
        run_globals = {
            "__file__": args.path,
            "__name__": "__main__",
            "__package__": None,
            "__cached__": None,
        }
        with AsyncioTracer() as at:
            exec(code, run_globals)

    trace = at.get_trace()
    if args.output:
        with open(args.output, "w") as output_file:
            output_file.write(str(trace))
    else:
        print(str(trace), file=sys.stderr)


if __name__ == "__main__":
    main()
