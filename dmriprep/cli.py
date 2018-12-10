# -*- coding: utf-8 -*-

"""Console script for dmriprep."""
import sys
import click
from . import run
from . import io
from .data import get_dataset
import os


@click.command()
@click.option('--participant-label', help="The label(s) of the participant(s) that should be"
                                           "analyzed. The label corresponds to"
                                           "sub-<participant_label> from the BIDS spec (so it does"
                                           "not include 'sub-'). If this parameter is not provided"
                                           "all subjects will be analyzed. Multiple participants"
                                           "can be specified with a space separated list.",
              default=None
              )
@click.argument('bids_dir',
                )
@click.argument('output_dir',
                )
@click.argument('analysis_level',
                type=click.Choice(['participant', 'group']),
                default='participant')
def main(participant_label, bids_dir, output_dir, analysis_level="participant"):
    """
    BIDS_DIR: The directory with the input dataset formatted according to the BIDS standard.

    OUTPUT_DIR: The directory where the output files should be stored.
    If you are running a group level analysis, this folder
    should be prepopulated with the results of
    the participant level analysis.

    ANALYSIS_LEVEL: Level of the analysis that will be performed. Multiple
    participant level analyses can be run independently
    (in parallel).
    """

    if analysis_level is not 'participant':
        raise NotImplementedError('The only valid analysis level for dmriprep is participant at the moment.')

    inputs = io.get_bids_files(participant_label, bids_dir)

    for subject_inputs in inputs:
        run.run_dmriprep_pe(**subject_inputs,
                            working_dir=os.path.join(output_dir, 'scratch'),
                            out_dir=output_dir)

    return 0

@click.command()
@click.argument('output_dir',
                )
def data(output_dir):
    get_dataset(os.path.abspath(output_dir))
    print('done')


@click.command()
@click.argument('output_dir')
@click.argument('bucket')
@click.option('--access_key', help="your AWS access key")
@click.option('--secret_key', help="your AWS access secret")
@click.option('--provider', default='s3', help="Cloud storage provider. Only S3 is supported right now.")
@click.option('--subject', default=None, help="Subject id to upload (optional)")
def upload(output_dir, bucket, access_key, secret_key, provider='s3', subject=None):
    """
    OUTPUT_DIR: The directory where the output files were stored.

    BUCKET: The cloud bucket name to upload data to.
    """

    import boto3
    from glob import glob

    output_dir = os.path.abspath(output_dir)
    if not output_dir.endswith('/'):
        output_dir += '/'

    if provider == 's3' or provider == 'S3':
        client = boto3.client('s3',  aws_access_key_id=access_key, aws_secret_access_key=secret_key)

        if subject is not None:
            assert os.path.exists(os.path.join(output_dir, subject)), 'this subject id does not exist!'
            subjects = [subject]
        else:
            subjects = [os.path.split(s)[1] for s in glob(os.path.join(output_dir, 'sub-*'))]

        for s in subjects:
            base_dir = os.path.join(output_dir, s, 'dmriprep')
            for root, dirs, files in os.walk(base_dir):
                for f in files:
                    filepath = os.path.join(root, f)
                    key = root.replace(output_dir, '')
                    # TODO: progress bar on this!!
                    client.upload_file(filepath, bucket, os.path.join(key, f))



    else:
        raise NotImplementedError('Only S3 is the only supported provider for data uploads at the moment')


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
