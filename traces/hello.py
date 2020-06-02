#!/bin/env python3

import dis
import sys

def test():
    print(f"Hello, World", file=sys.stderr)

def main():
    test()

if __name__ == "__main__":
    dis.dis(main)
