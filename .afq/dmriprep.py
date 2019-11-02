# -*- coding: utf-8 -*-

"""Main module."""

import logging
import os
import os.path as op
import subprocess

from .run import run_dmriprep


mod_logger = logging.getLogger(__name__)
