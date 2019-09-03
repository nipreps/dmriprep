# -*- coding: utf-8 -*-

"""Console script for dmriprep."""
import os
import sys
import warnings
from multiprocessing import cpu_count

import click
from bids import BIDSLayout
from nipype import config as ncfg

from .utils.bids import collect_participants
from .workflows.base import init_dmriprep_wf

# Filter warnings that are visible whenever you import another package that
# was compiled against an older numpy than is installed.
warnings.filterwarnings('ignore', message='numpy.dtype size changed')
warnings.filterwarnings('ignore', message='numpy.ufunc size changed')


@click.command()
# arguments as specified by BIDS-Apps
@click.argument('bids_dir', type=click.Path(exists=True, file_okay=False))
@click.argument(
    'output_dir', type=click.Path(exists=True, file_okay=False, writable=True)
)
@click.argument(
    'analysis_level',
    default='participant',
    type=click.Choice(['participant', 'group'])
)
# optional arguments
# options for filtering BIDS queries
@click.option(
    '--skip_bids_validation',
    help='Assume the input dataset is BIDS compliant and skip the validation',
    is_flag=True
)
@click.option(
    '--participant_label',
    default=None,
    help='The label(s) of the participant(s) that should be '
    'analyzed. The label corresponds to '
    'sub-<participant_label> from the BIDS spec (the "sub-" '
    'prefix can be removed). If this parameter is not provided '
    'all subjects will be analyzed. Multiple participants '
    'can be specified with a space delimited list.',
    multiple=True
)
@click.option(
    '--session_label',
    default=None,
    help='The label(s) of session(s) that should be analyzed. '
         'the label corresponds to ses-<session_label from the '
         'BIDS spec (the "ses-" prefix can be removed). If this '
         'parameter is not provided, all sessions will be '
         'analyzed. Multiple sessions can be specified with '
         'a space delimited list.',
    multiple=True
)
# options for prepping dwi scans
@click.option(
    '--concat_dwis',
    default=None,
    help='A space delimited list of acq-<label>',
    multiple=True
)
@click.option(
    '--b0_thresh',
    default=5,
    show_default=True,
    help='Threshold for b0 value',
    type=click.IntRange(min=0, max=10)
)
@click.option(
    '--output_resolution',
    help='The isotropic voxel size in mm the data will be resampled to before eddy.',
    type=float,
    multiple=True
)
@click.option(
    '--bet_dwi',
    default=0.3,
    show_default=True,
    help='Fractional intensity threshold for BET on the DWI. '
    'A higher value will be more strict; it will cut off more '
    'around what it analyzes the brain to be.',
    type=click.FloatRange(min=0, max=1)
)
@click.option(
    '--bet_mag',
    default=0.3,
    show_default=True,
    help='Fractional intensity threshold for BET on the magnitude. '
    'A higher value will be more strict; it will cut off more '
    'around what it analyzes the brain to be.',
    type=click.FloatRange(min=0, max=1)
)
# specific options for eddy
@click.option(
    '--acqp_file',
    default=None,
    help='If you want to pass in an acqp file for topup/eddy instead of'
    'generating it from the json by default.',
    type=click.Path(exists=True, dir_okay=False)
)
# workflow configuration
@click.option(
    '--nthreads',
    default=1,
    show_default=True,
    help='Maximum number of threads across all processes',
    type=int
)
@click.option(
    '--omp_nthreads',
    default=1,
    show_default=True,
    help='Maximum number of threads per process',
    type=int
)
@click.option(
    '--ignore',
    '-i',
    help='Specify which node(s) to skip during the preprocessing of the dwi.',
    type=click.Choice(['denoising', 'unringing', 'fieldmaps']),
    multiple=True
)
@click.option(
    '--work_dir',
    '-w',
    help='working directory',
    type=click.Path(exists=True, file_okay=False, writable=True)
)
@click.option(
    '--synb0_dir',
    default=None,
    help='If you want to use Synb0-DISCO for preprocessing.',
    type=click.Path(exists=True, file_okay=False)
)
@click.option(
    '--write_graph',
    is_flag=True,
    default=False,
    help='Write out nipype workflow graph.',
    type=bool
)
def main(
    bids_dir,
    output_dir,
    analysis_level,
    skip_bids_validation,
    participant_label,
    session_label,
    concat_dwis,
    b0_thresh,
    output_resolution,
    bet_dwi,
    bet_mag,
    acqp_file,
    nthreads,
    omp_nthreads,
    ignore,
    work_dir,
    synb0_dir,
    write_graph
):
    """
    BIDS_DIR: The directory with the input dataset formatted according to the
    BIDS standard.

    OUTPUT_DIR: The directory where the output files should be stored. If you
    are running a group level analysis, this folder should be prepopulated with
    the results of the participant level analysis.

    ANALYSIS_LEVEL: Level of the analysis that will be performed. Multiple
    participant level analyses can be run independently (in parallel).
    """

    if analysis_level != 'participant':
        raise NotImplementedError(
            'The only valid analysis level for dmriprep '
            'is participant at the moment.'
        )

    layout = BIDSLayout(bids_dir, validate=True)
    subject_list = collect_participants(
        layout, participant_label=participant_label
    )

    if not skip_bids_validation:
        from .utils.bids import validate_input_dir
        validate_input_dir(bids_dir, subject_list)

    if not work_dir:
        work_dir = os.path.join(output_dir, 'scratch')

    if len(output_resolution) == 1:
        output_resolution = output_resolution * 3

    log_dir = os.path.join(output_dir, 'dmriprep', 'logs')

    plugin_settings = {
        'plugin': 'MultiProc',
        'plugin_args': {
            'raise_insufficient': False,
            'maxtasksperchild': 1,
            'n_procs': nthreads
        }
    }

    if omp_nthreads == 0:
        omp_nthreads = min(nthreads - 1 if nthreads > 1 else cpu_count(), 8)

    ncfg.update_config({
        'logging': {
            'log_directory': log_dir,
            'log_to_file': True
        },
        'execution': {
            'crashdump_dir': log_dir,
            'crashfile_format': 'txt',
            'remove_unnecessary_outputs': False,
            'keep_inputs': True,
            'get_linked_libs': False,
            'stop_on_first_crash': True
        },
        'monitoring': {
            'enabled': True,
            'sample_frequency': '0.5',
            'summary_append': True
        }
    })

    wf = init_dmriprep_wf(
        layout=layout,
        output_dir=output_dir,
        subject_list=subject_list,
        session_list=list(session_label),
        concat_dwis=list(concat_dwis),
        b0_thresh=b0_thresh,
        output_resolution=output_resolution,
        bet_dwi=bet_dwi,
        bet_mag=bet_mag,
        acqp_file=acqp_file,
        omp_nthreads=omp_nthreads,
        ignore=list(ignore),
        work_dir=work_dir,
        synb0_dir=synb0_dir
    )

    if write_graph:
        wf.write_graph(graph2use='colored', format='svg', simple_form=True)

    wf.run(**plugin_settings)

    return 0


if __name__ == '__main__':
    sys.exit(main())  # pragma: no cover
