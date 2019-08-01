#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" dmriprep setup script """

import sys
from setuptools import setup, find_packages
from setuptools.extension import Extension
import versioneer

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
]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

extras_require = {"dev": ["flake8", "pytest", "pytest-cov", "pre-commit"]}

setup(
    # project information
    name="dmriprep",
    version="0.1.0",
    author="Michael Joseph",
    author_email="michael.joseph@camh.ca",
    url="https://github.com/tigrlab/dmriprep",
    license="BSD license",
    # description
    description="Preprocessing of diffusion MRI data",
    long_description=readme + "\n\n" + history,
    # requirements
    python_requires=">=3.5",
    install_requires=requirements,
    setup_requires=setup_requirements,
    extras_require=extras_require,
    # packaging
    packages=find_packages(include=["dmriprep*"]),
    include_package_data=True,
    zip_safe=False,
    # tests
    test_suite="tests",
    tests_require=test_requirements,
    # cli
    entry_points={"console_scripts": ["dmriprep=dmriprep.cli:main"]},
    # metadata
    keywords="diffusion-mri diffusion-preprocessing bids",
    project_urls={
        "Documentation": "https://dmriprep.readthedocs.io/en/latest/",
        "Tracker": "https://github.com/TIGRLab/dmriprep/issues/",
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
