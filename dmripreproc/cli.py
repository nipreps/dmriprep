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
        ignore_nodes,
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
        self.ignore_nodes = ignore_nodes
        self.resize_scale = resize_scale
        self.b0_thresh = b0_thresh
        self.bet_dwi = bet_dwi
        self.bet_mag = bet_mag
        self.eddy_niter = eddy_niter
        self.synb0_dir = synb0_dir
        self.acqp_file = acqp_file


@click.command()
@click.argument("bids_dir", type=click.Path())
@click.argument("output_dir", type=click.Path())
@click.argument(
    "analysis_level",
    default="participant",
    type=click.Choice(["participant", "group"]),
)
@click.option(
    "--skip_bids_validation", help="Skip BIDS validation", is_flag=True
)
@click.option(
    "--participant_label",
    help="The label(s) of the participant(s) that should be "
    "analyzed. The label corresponds to "
    "sub-<participant_label> from the BIDS spec (the 'sub-' "
    "prefix can be removed). If this parameter is not provided "
    "all subjects will be analyzed. Multiple participants "
    "can be specified with a space delimited list.",
    default=None,
)
@click.option(
    "--concat_shells",
    help="A space delimited list of acq-<label>",
    default=None,
)
@click.option(
    "--b0_thresh", help="Threshold for b0 value", default=5, type=(int)
)
@click.option(
    "--resize_scale", help="Scale factor to resize DWI image", type=(float)
)
@click.option(
    "--eddy_niter",
    help="Fixed number of eddy iterations. See "
    "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide"
    "#A--niter",
    default=5,
    type=(int),
)
@click.option(
    "--bet_dwi",
    help="Fractional intensity threshold for BET on the DWI. "
    "A higher value will be more strict; it will cut off more "
    "around what it analyzes the brain to be. "
    "If this parameter is not provided a default of 0.3 will "
    "be used.",
    default=0.3,
    type=(float),
)
@click.option(
    "--bet_mag",
    help="Fractional intensity threshold for BET on the magnitude. "
    "A higher value will be more strict; it will cut off more "
    "around what it analyzes the brain to be. "
    "If this parameter is not provided a default of 0.3 will "
    "be used.",
    default=0.3,
    type=(float),
)
@click.option(
    "--acqp_file",
    help="If you want to pass in an acqp file for topup/eddy instead of"
    "generating it from the json by default.",
    default=None,
    type=click.Path(),
)
@click.option(
    "--ignore_nodes",
    help="Specify which node(s) to skip during the preprocessing of the dwi."
    "Example: If you want to skip unring and resize, use '--ignore_nodes ur'."
    "Options are: \n"
    "   d: denoise \n"
    "   u: unring \n"
    "   r: resize (upsample)",
    default="r",
    type=(str),
)
@click.option("--work_dir", help="working directory", type=click.Path())
@click.option(
    "--synb0_dir",
    help="If you want to use Synb0-DISCO for preprocessing.",
    default=None,
    type=click.Path(),
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
    ignore_nodes,
    synb0_dir,
    acqp_file,
):
    """
    BIDS_DIR: The directory with the input dataset formatted according to
    the BIDS standard.

    OUTPUT_DIR: The directory where the output files should be stored.
    If you are running a group level analysis, this folder
    should be prepopulated with the results of
    the participant level analysis.

    ANALYSIS_LEVEL: Level of the analysis that will be performed. Multiple
    participant level analyses can be run independently
    (in parallel).
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
        ignore_nodes=ignore_nodes,
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
