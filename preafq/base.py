import os.path as op
from collections import namedtuple
from pathlib import Path

import boto3

# Define the different namedtuple return types
InputS3Keys = namedtuple(
    'InputS3Keys',
    ['subject', 'site', 'valid', 's3_keys']
)

# Input files namedtuple
InputFiles = namedtuple('InputFiles', ['subject', 'site', 'files'])


def download_prereqs(subject_keys, bucket='fcp-indi', directory='./input'):
    """
    Parameters
    ----------
    subject_keys : InputS3Keys namedtuple
        Input s3 keys stored in namedtuple. Must have the fields
        'subject': subjectID,
        'site': siteID,
        's3_keys': dictionary of S3 keys

    bucket : string
        S3 bucket from which to extract files

    directory : string
        Local directory to which to save files

    Returns
    -------
    files : InputFiles namedtuple
        Input file paths stored in namedtuple. Has the fields
        'subject': subjectID,
        'site' : siteID,
        'files' : local file paths
    """
    s3 = boto3.client('s3')
    subject = subject_keys.subject
    site = subject_keys.site

    input_files = InputFiles(
        subject=subject,
        site=site,
        files={
            k: [op.abspath(op.join(
                directory, site, p.split('/' + site + '/')[-1]
            )) for p in v] for k, v in subject_keys.s3_keys.items()
        },
    )

    s3keys = subject_keys.s3_keys
    files = input_files.files
    for ftype in s3keys.keys():
        for key, fname in zip(s3keys[ftype], files[ftype]):
            # Create the directory and file if necessary
            Path(op.dirname(fname)).mkdir(parents=True, exist_ok=True)
            Path(fname).touch(exist_ok=True)

            # Download the file
            s3.download_file(Bucket=bucket, Key=key, Filename=fname)

    return input_files


def upload_to_s3(output_files, bucket, prefix, site, session, subject):
    """Upload output files to S3, using key format specified by input params

    Parameters
    ----------
    output_files : dict of filenames
        Output files to transfer to S3. Assume that the user has passed in
        relative paths that are appropriate to fill in after the 'preAFQ'
        directory.

    bucket : string
        Output S3 bucket

    prefix : string
        Output S3 prefix

    site : string
        Site ID, e.g. 'side-SI'

    session : string
        Session ID, e.g. 'sess-001'

    subject : string
        Subject ID, e.g. 'sub-ABCXYZ'

    Returns
    -------
    dict
        S3 keys for each output file. The dict keys are the same as the keys
        for the input parameter `output_files`
    """
    s3 = boto3.client('s3')

    def filename2s3key(filename):
        return '/'.join([
            prefix, site, subject, session,
            'derivatives', 'preAFQ',
            op.basename(filename)
        ])

    for file in output_files.values():
        with open(file, 'rb') as fp:
            s3.put_object(
                Bucket=bucket,
                Body=fp,
                Key=filename2s3key(file),
            )

    return {k: filename2s3key(v) for k, v in output_files.items()}
