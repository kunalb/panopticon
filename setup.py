#!/bin/env python3

import setuptools
from os import path


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

version = {}
with open(
    path.join(this_directory, "panopticon/version.py"), encoding="utf-8"
) as v:
    exec(v.read(), version)
    assert "version" in version, "version.py must set the module version!"


setuptools.setup(
    name="panopticon",
    version=version["version"],
    author="Kunal Bhalla",
    author_email="bhalla.kunal@gmail.com",
    description="A python tracer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kunalb/panopticon",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
