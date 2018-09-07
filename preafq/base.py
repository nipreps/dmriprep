# -*- coding: utf-8 -*-

"""Base datatypes for preafq"""

from collections import namedtuple

# Define the different namedtuple return types
InputFiles = namedtuple(
    'InputFiles',
    ['subject', 'site', 'valid', 'files', 'file_type']
)

# Input files (one type with session info and one without)
InputFilesWithSession = namedtuple(
    'InputFilesWithSession',
    ['subject', 'site', 'session', 'files', 'file_type']
)
