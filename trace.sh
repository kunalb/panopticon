#!/bin/sh

set -e -x

echo $$
echo $$ > /sys/kernel/tracing/set_ftrace_pid
echo function > /sys/kernel/tracing/current_tracer
echo :mod:sched > /sys/kernel/tracing/set_ftrace_filter
echo 1 > /sys/kernel/tracing/events/sched/enable
echo > /sys/kernel/tracing/trace
echo 1 > /sys/kernel/tracing/tracing_on
$*
cat /sys/kernel/tracing/trace > ftrace.txt
echo 0 > /sys/kernel/tracing/tracing_on
