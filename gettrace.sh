#!/bin/sh

set -e -x

cat /sys/kernel/tracing/trace > ftrace.txt
echo 0 > /sys/kernel/tracing/tracing_on
