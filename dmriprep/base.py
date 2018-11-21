# -*- coding: utf-8 -*-

"""Base datatypes for dmriprep"""

from collections import namedtuple

import boto3
from botocore import UNSIGNED
from botocore.client import Config


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

# Global s3 client to preserve anonymous config
s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
