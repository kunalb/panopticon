#!/bin/env python3

import setuptools

setuptools.setup(
    name="panopticon-knl",
    version="0.0.1",
    author="Kunal Bhalla",
    author_email="bhalla.kunal@gmail.com",
    description="A python tracer",
    long_description="TODO",
    long_description_content_type="text/markdown",
    url="https://github.com/kunalb/panopticon",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
