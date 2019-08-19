#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Top-level package for dmriprep."""

from .__about__ import (
    __version__,
    __credits__,
    __packagename__
)

import warnings

# Filter warnings that are visible whenever you import another package that
# was compiled against an older numpy than is installed.
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")
