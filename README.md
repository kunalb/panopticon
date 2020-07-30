Panopticon
==========

Panopticon is a debugger-powered tracer for Python code to
quickly visualize and explore code execution. Traces generated are
\[Catapult\](<https://chromium.googlesource.com/catapult/+/HEAD/tracing/README.md>)
compatible -- available at \`chrome://tracing\` if you\'re using Chrome.

Usage
-----

### Run a command directly

``` {.python}
python3 -m panopticon -c "print('hello') -o print_hello.trace
```

### Run a file

``` {.python}
python3 -m panopticon custom_file.py -o file.trace
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

Python supports suspending and continuing execution of a frame through
generators, coroutines and asynchronous generators. Panopticon creates
\"flow\" events to connect a single frame executing through time, making
it easier to visualize what\'s actually happening.

Changelog
---------

### 0.0.1

-   Initial version of Panopticon
-   CLI supports running commands and files for tracing

Releases
--------

-   0.0.1 Initial release.
