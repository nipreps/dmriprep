#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "Click>=6.0",
    "dipy",
    "nipype>=1.2.0",
    "pandas",
    "parse",
    "tqdm",
    "pybids>=0.9.1",
    "matplotlib",
    "numba",
    "sphinx",
]

extras_require = {"dev": ["flake8", "pytest", "pytest-cov", "pre-commit"]}

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author="Anisha Keshavan",
    author_email="keshavan@berkeley.edu",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Preprocessing of neuroimaging data in preparation for AFQ analysis",
    entry_points={
        "console_scripts": [
            "dmripreproc=dmripreproc.cli:main",
            "dmripreproc-data=dmripreproc.cli:data",
            "dmripreproc-upload=dmripreproc.cli:upload",
        ]
    },
    install_requires=requirements,
    extras_require=extras_require,
    license="BSD license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="dmripreproc",
    name="dmripreproc",
    packages=find_packages(include=["dmripreproc*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/nipy/dmripreproc",
    version="0.1.0",
    zip_safe=False,
)
