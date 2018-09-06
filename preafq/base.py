# -*- coding: utf-8 -*-

"""Base datatypes for preafq"""

from collections import namedtuple

# Define the different namedtuple return types
InputS3Keys = namedtuple(
    'InputS3Keys',
    ['subject', 'site', 'valid', 's3_keys']
)

# Input files namedtuple
InputFiles = namedtuple('InputFiles', ['subject', 'site', 'files'])

