Panopticon
==========
[![License: MIT](https://img.shields.io/pypi/l/panopticon)](https://github.com/kunalb/panopticon/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Alpha](https://img.shields.io/badge/State-Alpha-red)


Panopticon is a debugger-powered tracer for Python code to quickly visualize and explore code execution. Traces generated are [Catapult](<https://chromium.googlesource.com/catapult/+/HEAD/tracing/README.md>) compatible — available at \`chrome://tracing\` if you\'re using Chrome. 

**Alpha**: I'm still working on adding tests, polishing the api, and cleaning up the code in general. It should be handy as a debugging tool -- and please report issues if you come across bugs!

![Sample trace with async functions](https://github.com/kunalb/panopticon/blob/master/images/async_hello.png?raw=true)


Usage
-----

You can read a more detailed guide with several examples of simple Python programs, different interfaces to visualize them and the corresponding traces at [explog.in/panopticon](https://explog.in/panopticon/index.html).


### Run a command directly

```sh
python3 -m panopticon -c "print('hello')" -o print_hello.trace
```

### Run a file

```sh
python3 -m panopticon -o file.trace file.py 
```

### In code

```python
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


