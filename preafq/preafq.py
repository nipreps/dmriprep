# -*- coding: utf-8 -*-

"""Main module."""

import logging
import os
import os.path as op

import boto3
import nibabel as nib

from . import fetch_bids_s3 as fetch
from .run_1 import run_preAFQ


mod_logger = logging.getLogger(__name__)


def move_t1_to_freesurfer(t1_file):
    """Move the T1 file back into the freesurfer directory.

    This step is specific to the HBN dataset where the T1 files
    are outside of the derivatives/sub-XXX/freesurfer directory.

    Parameters
    ----------
    t1_file : string
        Path to the T1 weighted nifty file
    """
    freesurfer_path = op.join(op.dirname(t1_file), 'freesurfer')

    img = nib.load(t1_file)
    img.to_filename(op.join(freesurfer_path, 'mri', 'orig.mgz'))


def upload_to_s3(output_files, bucket, prefix, site, session, subject):
    """Upload output files to S3, using key format specified by input params

    Parameters
    ----------
    output_files : list
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
            filename
        ])

    for file in output_files:
        with open(file, 'rb') as fp:
            s3.put_object(
                Bucket=bucket,
                Body=fp,
                Key=filename2s3key(file),
            )

    return {k: filename2s3key(v) for k, v in output_files.items()}


def pre_afq_individual(input_s3_keys, s3_prefix, out_bucket,
                       in_bucket='fcp-indi', workdir='.'):
    input_files = fetch.download_register(
        subject_keys=input_s3_keys,
        bucket=in_bucket,
        directory=op.abspath(op.join(workdir, 'input')),
    )

    scratch_dir = op.join(workdir, 'scratch')
    out_dir = op.join(workdir, 'output')

    run_preAFQ(
        dwi_file=input_files.files['dwi'],
        dwi_file_AP=input_files.files['epi_ap'],
        dwi_file_PA=input_files.files['epi_pa'],
        bvec_file=input_files.files['bvec'],
        bval_file=input_files.files['bval'],
        subjects_dir=op.dirname(input_files.files['t1w']),
        working_dir=scratch_dir,
        out_dir=out_dir,
    )

    out_files = []
    for root, dirs, filenames in os.walk(out_dir):
        for filename in filenames:
            rel_path = op.join(root, filename)
            if op.isfile(rel_path):
                out_files.append(rel_path.replace(out_dir + '/', '', 1))

    upload_to_s3(output_files=out_files,
                 bucket=out_bucket,
                 prefix=s3_prefix,
                 site=input_s3_keys.site,
                 session=input_s3_keys.session,
                 subject=input_s3_keys.subject)
