# -*- coding: utf-8 -*-

"""Console script for dmriprep."""
import os
import sys
import warnings

import click
from bids import BIDSLayout

from .utils.bids import collect_participants
from .workflows.base import init_dmriprep_wf

# Filter warnings that are visible whenever you import another package that
# was compiled against an older numpy than is installed.
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

@click.command()
# arguments as specified by BIDS-Apps
@click.argument("bids_dir", type=click.Path(exists=True, file_okay=False))
@click.argument(
    "output_dir", type=click.Path(exists=True, file_okay=False, writable=True)
)
@click.argument(
    "analysis_level", default="participant", type=click.Choice(["participant", "group"])
)
# optional arguments
# options for filtering BIDS queries
@click.option(
    "--skip_bids_validation",
    help="Assume the input dataset is BIDS compliant and skip the validation",
    is_flag=True
)
@click.option(
    "--participant_label",
    default=None,
    help="The label(s) of the participant(s) that should be "
    "analyzed. The label corresponds to "
    "sub-<participant_label> from the BIDS spec (the 'sub-' "
    "prefix can be removed). If this parameter is not provided "
    "all subjects will be analyzed. Multiple participants "
    "can be specified with a space delimited list."
)
# options for prepping dwi scans
# @click.option(
#     "--concat_shells",
#     default=None,
#     help="A space delimited list of acq-<label>",
# )
@click.option(
    "--b0_thresh",
    default=5,
    show_default=True,
    help="Threshold for b0 value",
    type=click.IntRange(min=0, max=10),
)
@click.option(
    "--output_resolution",
    help="The isotropic voxel size in mm the data will be resampled to before eddy.",
    type=float,
    multiple=True
)
# specific options for eddy
@click.option(
    "--omp_nthreads",
    default=1,
    show_default=True,
    help="Maximum number of threads for eddy",
    type=int,
)
@click.option(
    "--eddy_niter",
    default=5,
    show_default=True,
    help="Fixed number of eddy iterations. See "
    "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide"
    "#A--niter",
    type=int,
)
@click.option(
    "--bet_dwi",
    default=0.3,
    show_default=True,
    help="Fractional intensity threshold for BET on the DWI. "
    "A higher value will be more strict; it will cut off more "
    "around what it analyzes the brain to be.",
    type=click.FloatRange(min=0, max=1),
)
@click.option(
    "--bet_mag",
    default=0.3,
    show_default=True,
    help="Fractional intensity threshold for BET on the magnitude. "
    "A higher value will be more strict; it will cut off more "
    "around what it analyzes the brain to be.",
    type=click.FloatRange(min=0, max=1),
)
@click.option(
    "--acqp_file",
    default=None,
    help="If you want to pass in an acqp file for topup/eddy instead of"
    "generating it from the json by default.",
    type=click.Path(exists=True, dir_okay=False),
)
# workflow configuration
@click.option(
    "--ignore",
    "-i",
    help="Specify which node(s) to skip during the preprocessing of the dwi.",
    type=click.Choice(["denoise", "unring"]),
    multiple=True,
)
@click.option(
    "--work_dir",
    "-w",
    help="working directory",
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option(
    "--synb0_dir",
    default=None,
    help="If you want to use Synb0-DISCO for preprocessing.",
    type=click.Path(exists=True, file_okay=False),
)
def main(
    participant_label,
    bids_dir,
    output_dir,
    analysis_level,
    skip_bids_validation,
    work_dir,
    ignore,
    b0_thresh,
    output_resolution,
    bet_dwi,
    bet_mag,
    omp_nthreads,
    eddy_niter,
    synb0_dir,
    acqp_file
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

    if analysis_level != "participant":
        raise NotImplementedError(
            "The only valid analysis level for dmriprep "
            "is participant at the moment."
        )

    layout = BIDSLayout(bids_dir, validate=True)
    all_subjects, subject_list = collect_participants(
        layout, participant_label=participant_label
    )

    if not skip_bids_validation:
        from .utils.bids import validate_input_dir

        validate_input_dir(bids_dir, all_subjects, subject_list)

    if not work_dir:
        work_dir = os.path.join(output_dir, "scratch")

    if len(output_resolution) == 1:
        output_resolution = output_resolution * 3

    wf = init_dmriprep_wf(
        subject_list=subject_list,
        layout=layout,
        output_dir=output_dir,
        work_dir=work_dir,
        ignore=list(ignore),
        b0_thresh=b0_thresh,
        output_resolution=output_resolution,
        bet_dwi=bet_dwi,
        bet_mag=bet_mag,
        omp_nthreads=omp_nthreads,
        synb0_dir=synb0_dir
    )
    wf.write_graph()
    wf.config["execution"]["remove_unnecessary_outputs"] = False
    wf.config["execution"]["keep_inputs"] = True
    wf.config["execution"]["crashfile_format"] = "txt"
    wf.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
