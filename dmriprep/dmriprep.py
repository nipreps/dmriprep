# -*- coding: utf-8 -*-

"""Main module."""

import logging
import os
import os.path as op
import subprocess

from .run import run_dmriprep


mod_logger = logging.getLogger(__name__)



def pre_afq_individual(input_s3_keys, s3_prefix, out_bucket,
                       in_bucket='fcp-indi', workdir=op.abspath('.')):
    input_files = fetch.download_register(
        subject_keys=input_s3_keys,
        bucket=in_bucket,
        directory=op.abspath(op.join(workdir, 'input')),
    )

    move_t1_to_freesurfer(input_files.files['t1w'][0])

    scratch_dir = op.join(workdir, 'scratch')
    out_dir = op.join(workdir, 'output')

    run_dmriprep(
        dwi_file=input_files.files['dwi'][0],
        dwi_file_AP=input_files.files['epi_ap'][0],
        dwi_file_PA=input_files.files['epi_pa'][0],
        bvec_file=input_files.files['bvec'][0],
        bval_file=input_files.files['bval'][0],
        subjects_dir=op.dirname(input_files.files['t1w'][0]),
        working_dir=scratch_dir,
        out_dir=out_dir,
    )

    out_files = []
    for root, dirs, filenames in os.walk(out_dir):
        for filename in filenames:
            rel_path = op.join(root, filename)
            if op.isfile(rel_path):
                out_files.append(rel_path.replace(out_dir + '/', '', 1))

    s3_output = upload_to_s3(output_files=out_files,
                             outdir=out_dir,
                             bucket=out_bucket,
                             prefix=s3_prefix,
                             site=input_s3_keys.site,
                             session=input_s3_keys.session,
                             subject=input_s3_keys.subject)

    return s3_output
