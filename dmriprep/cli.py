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
@click.option('--eddy-niter',
              help="Fixed number of eddy iterations. See"
                   "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide#A--niter",
              default=5)
@click.option('--slice-outlier-threshold',
              help="Number of allowed outlier slices per volume."
                   "If this is exceeded the volume is dropped from analysis. If"
                   "`slice_outlier_threshold` is an int, it is treated as number of allowed"
                   "outlier slices. If `slice_outlier_threshold` is a float between 0 and 1"
                   "(exclusive), it is treated the fraction of allowed outlier slices.",
              default=0.02)
@click.argument('bids_dir',
                )
@click.argument('output_dir',
                )
@click.argument('analysis_level',
                type=click.Choice(['participant', 'group']),
                default='participant')
def main(participant_label, bids_dir, output_dir,
         eddy_niter=5, slice_outlier_threshold=0.02,
         analysis_level="participant"):
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
                            out_dir=output_dir,
                            eddy_niter=eddy_niter,
                            slice_outlier_threshold=slice_outlier_threshold)

    return 0

@click.command()
@click.argument('output_dir',
                )
def data(output_dir):
    get_dataset(os.path.abspath(output_dir))
    print('done')


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
