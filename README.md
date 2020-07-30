Panopticon
==========

Panopticon is a debugger-powered tracer for Python code to quickly visualize and explore code execution. Traces generated are [Catapult](<https://chromium.googlesource.com/catapult/+/HEAD/tracing/README.md>) compatible — available at \`chrome://tracing\` if you\'re using Chrome. 

![Sample trace with async functions](https://github.com/kunalb/panopticon/blob/master/images/async_hello.png?raw=true)

Motivation & Internals 
----------------------

Python already has an excellent tracer module, but I wanted a more convenient way to observe what's actually going on across threads and coroutines. I'd used Catapult in a past life while working on Android, and that seemed like an excellent way to quickly get detailed visualizations of code execution that I could parse.

The current version is fairly simple, and relies on [Python's setprofile](https://explog.in/notes/settrace.html) to observe function transitions. Coroutines and other "continuable" frames are identified by their location in memory, and "closed" when they end with a RETURN_VALUE opcode.

Usage
-----

### Run a command directly

``` {.python}
python3 -m panopticon -c "print('hello') -o print_hello.trace
```

### Run a file

``` {.python}
python3 -m panopticon -o file.trace file.py 
```

### In code

``` {.python}
with panopticon.tracer.AsyncTracer() as at:
    print("Hello")

with open("print_hello.trace", "w") as outfile:
    outfile.write(str(at))
```

Asynchronous Functions
----------------------

Python supports suspending and continuing execution of a frame through generators, coroutines and asynchronous generators. Panopticon creates \"flow\" events to connect a single frame executing through time, making it easier to visualize what\'s actually happening.

You can enable/disable connections for different types of functions by choosing to enable/disable flow events in Catpult (top-right).

Changelog
---------

### 0.0.1

-   Initial version of Panopticon
-   CLI supports running commands and files for tracing


