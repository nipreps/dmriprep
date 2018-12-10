# -*- coding: utf-8 -*-

"""Top-level package for dmriprep."""

__author__ = """Anisha Keshavan"""
__email__ = 'anishakeshavan@gmail.com'
__version__ = '0.1.0'

import errno
import logging
import os

from . import data
from . import io
from . import qc
from . import run

module_logger = logging.getLogger(__name__)

# get the log level from environment variable
if "DMIRPREP_LOGLEVEL" in os.environ:
    loglevel = os.environ['DMRIPREP_LOGLEVEL']
    module_logger.setLevel(getattr(logging, loglevel.upper()))
else:
    module_logger.setLevel(logging.WARNING)

# create a file handler
logpath = os.path.join(os.path.expanduser('~'), '.dmriprep', 'dmriprep.log')

# Create the config directory if it doesn't exist
logdir = os.path.dirname(logpath)
try:
    os.makedirs(logdir)
except OSError as e:
    pre_existing = (e.errno == errno.EEXIST and os.path.isdir(logdir))
    if pre_existing:
        pass
    else:
        raise e

handler = logging.FileHandler(logpath, mode='w')
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

# add the handlers to the logger
module_logger.addHandler(handler)
module_logger.info('Started new dmriprep session')
