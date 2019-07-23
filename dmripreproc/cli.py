# -*- coding: utf-8 -*-

"""Console script for dmripreproc."""
import os
import sys
import warnings
from bids import BIDSLayout

import click

from .utils.bids import collect_participants
from .workflows.base import init_dmripreproc_wf

# Filter warnings that are visible whenever you import another package that
# was compiled against an older numpy than is installed.
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")


class Parameters:
    def __init__(
        self,
        layout,
        subject_list,
        bids_dir,
        work_dir,
        output_dir,
        concat_shells,
        b0_thresh,
        resize_scale,
        eddy_niter,
        bet_dwi,
        bet_mag,
        ignore,
        analysis_level,
        synb0_dir,
        acqp_file,
    ):
        self.bids_dir = bids_dir
        self.output_dir = output_dir
        self.analysis_level = analysis_level
        self.layout = layout
        self.subject_list = subject_list
        self.work_dir = work_dir
        self.concat_shells = concat_shells
        self.ignore = ignore
        self.resize_scale = resize_scale
        self.b0_thresh = b0_thresh
        self.bet_dwi = bet_dwi
        self.bet_mag = bet_mag
        self.eddy_niter = eddy_niter
        self.synb0_dir = synb0_dir
        self.acqp_file = acqp_file


@click.command()
# arguments as specified by BIDS-Apps
@click.argument("bids_dir", type=click.Path(exists=True, file_okay=False))
@click.argument(
    "output_dir", type=click.Path(exists=True, file_okay=False, writable=True)
)
@click.argument(
    "analysis_level",
    default="participant",
    type=click.Choice(["participant", "group"]),
)
# optional arguments
# options for filtering BIDS queries
@click.option(
    "--skip_bids_validation", help="Skip BIDS validation", is_flag=True
)
@click.option(
    "--participant_label",
    default=None,
    help="The label(s) of the participant(s) that should be "
    "analyzed. The label corresponds to "
    "sub-<participant_label> from the BIDS spec (the 'sub-' "
    "prefix can be removed). If this parameter is not provided "
    "all subjects will be analyzed. Multiple participants "
    "can be specified with a space delimited list.",
)
# options for prepping dwi scans
@click.option(
    "--concat_shells",
    default=None,
    help="A space delimited list of acq-<label>",
)
@click.option(
    "--b0_thresh",
    default=5,
    show_default=True,
    help="Threshold for b0 value",
    type=click.IntRange(min=0, max=10),
)
@click.option(
    "--resize_scale", help="Scale factor to resize DWI image", type=float
)
# specific options for eddy
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
    "around what it analyzes the brain to be. "
    "If this parameter is not provided a default of 0.3 will "
    "be used.",
    type=click.FloatRange(min=0, max=1),
)
@click.option(
    "--bet_mag",
    default=0.3,
    show_default=True,
    help="Fractional intensity threshold for BET on the magnitude. "
    "A higher value will be more strict; it will cut off more "
    "around what it analyzes the brain to be. "
    "If this parameter is not provided a default of 0.3 will "
    "be used.",
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
    default="resample",
    show_default=True,
    help="Specify which node(s) to skip during the preprocessing of the dwi.",
    type=click.Choice(["denoise", "unring", "resample"]),
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
    work_dir,
    skip_bids_validation,
    analysis_level,
    b0_thresh,
    concat_shells,
    resize_scale,
    eddy_niter,
    bet_dwi,
    bet_mag,
    ignore,
    synb0_dir,
    acqp_file,
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
            "The only valid analysis level for dmripreproc "
            "is participant at the moment."
        )

    layout = BIDSLayout(bids_dir, validate=False)
    all_subjects, subject_list = collect_participants(
        layout, participant_label=participant_label
    )

    if not skip_bids_validation:
        from .utils.bids import validate_input_dir

        validate_input_dir(bids_dir, all_subjects, subject_list)

    if not work_dir:
        work_dir = os.path.join(output_dir, "scratch")

    # Set parameters based on CLI, pass through object
    parameters = Parameters(
        layout=layout,
        subject_list=subject_list,
        bids_dir=bids_dir,
        work_dir=work_dir,
        output_dir=output_dir,
        concat_shells=concat_shells,
        b0_thresh=b0_thresh,
        resize_scale=resize_scale,
        eddy_niter=eddy_niter,
        bet_dwi=bet_dwi,
        bet_mag=bet_mag,
        ignore=ignore,
        analysis_level=analysis_level,
        synb0_dir=synb0_dir,
        acqp_file=acqp_file,
    )

    wf = init_dmripreproc_wf(parameters)
    wf.write_graph(graph2use="colored")
    wf.config["execution"]["remove_unnecessary_outputs"] = False
    wf.config["execution"]["keep_inputs"] = True
    wf.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
