# -*- coding: utf-8 -*-

"""Top-level package for dmripreproc."""

__author__ = """Anisha Keshavan"""
__email__ = "anishakeshavan@gmail.com"
__version__ = "0.1.0"

import errno
import logging
import os
import warnings

# Filter warnings that are visible whenever you import another package that
# was compiled against an older numpy than is installed.
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

from . import qc

module_logger = logging.getLogger(__name__)

# get the log level from environment variable
if "DMIRPREP_LOGLEVEL" in os.environ:
    loglevel = os.environ["dmripreproc_LOGLEVEL"]
    module_logger.setLevel(getattr(logging, loglevel.upper()))
else:
    module_logger.setLevel(logging.WARNING)

# create a file handler
logpath = os.path.join(os.path.expanduser("~"), ".dmripreproc", "dmripreproc.log")

# Create the config directory if it doesn't exist
logdir = os.path.dirname(logpath)
try:
    os.makedirs(logdir)
except OSError as e:
    pre_existing = e.errno == errno.EEXIST and os.path.isdir(logdir)
    if pre_existing:
        pass
    else:
        raise e

handler = logging.FileHandler(logpath, mode="w")
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)

# add the handlers to the logger
module_logger.addHandler(handler)
module_logger.info("Started new dmripreproc session")
