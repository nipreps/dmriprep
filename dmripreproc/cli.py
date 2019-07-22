# -*- coding: utf-8 -*-

"""Console script for dmripreproc."""
import os
import sys
import warnings
from bids import BIDSLayout

import click

from . import utils
from .workflows.base import init_dmripreproc_wf

# Filter warnings that are visible whenever you import another package that
# was compiled against an older numpy than is installed.
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")


@click.command()
@click.option(
    "--participant-label",
    help="The label(s) of the participant(s) that should be "
    "analyzed. The label corresponds to "
    "sub-<participant_label> from the BIDS spec (so it does "
    "not include 'sub-'). If this parameter is not provided "
    "all subjects will be analyzed. Multiple participants "
    "can be specified with a space separated list.",
    default=None,
)
#@click.option(
#    "--ignore",
#    help="Ignore selected parts of the workflow.",
#    type=click.Choice(["denoise", "unring"]),
#)
@click.option(
    "--resize-scale", help="Scale factor to resize DWI image", type=(float)
)
@click.option(
    "--eddy-niter",
    help="Fixed number of eddy iterations. See "
    "https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy/UsersGuide"
    "#A--niter",
    default=5,
    type=(int),
)
@click.option(
    "--bet-dwi",
    help="Fractional intensity threshold for BET on the DWI. "
    "A higher value will be more strict; it will cut off more "
    "around what it analyzes the brain to be. "
    "If this parameter is not provided a default of 0.3 will "
    "be used.",
    default=0.3,
)
@click.option(
    "--bet-mag",
    help="Fractional intensity threshold for BET on the magnitude. "
    "A higher value will be more strict; it will cut off more "
    "around what it analyzes the brain to be. "
    "If this parameter is not provided a default of 0.3 will "
    "be used.",
    default=0.3,
)
@click.option(
    "--total-readout",
    help="Manual option for what value will be used in acquired params step. "
    "If this parameter is not provided the value will be taken from the "
    "TotalReadoutTime field in the dwi json. ",
    default=None,
    type=(float),
)
@click.option(
    "--ignore_nodes",
    help="Specify which node(s) to skip during the preprocessing of the dwi."
    "Example: If you want to skip unring and resize, use '--ignore_nodes ur'."
    "Options are: \n"
    "   d: denoise \n"
    "   u: unring \n"
    "   r: resize (upsample)",
    default=None,
    type=(str),
)
@click.option(
    "--synb0_dir",
    help="If you want to use Synb0-DISCO for preprocessing.",
    #is_flag=True
    default=None,
    type=(str),
)
@click.option(
    "--acqp_file",
    help="If you want to pass in an acqp file for topup/eddy instead of"
    "generating it from the json by default.",
    #is_flag=True
    default=None,
    type=(str),
)
@click.argument("bids_dir")
@click.argument("output_dir")
@click.argument(
    "analysis_level",
    type=click.Choice(["participant", "group"]),
    default="participant",
)
def main(
    participant_label,
    bids_dir,
    output_dir,
    resize_scale,
    eddy_niter=5,
    bet_dwi=0.3,
    bet_mag=0.3,
    total_readout=None,
    ignore_nodes="",
    analysis_level="participant",
    synb0_dir=None,
    acqp_file=None,
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

    if analysis_level is not "participant":
        raise NotImplementedError(
            "The only valid analysis level for dmripreproc "
            "is participant at the moment."
        )

    layout = BIDSLayout(bids_dir, validate=False)
    print(layout)
    subject_list = utils.collect_participants(
        layout, participant_label=participant_label
    )

    work_dir = os.path.join(output_dir, "scratch")

    # Set parameters based on CLI, pass through object
    parameters = utils.Parameters()
    parameters.participant_label = participant_label
    parameters.layout = layout
    parameters.subject_list = subject_list
    parameters.bids_dir = bids_dir
    parameters.work_dir = work_dir
    parameters.output_dir = output_dir
    parameters.eddy_niter = eddy_niter
    parameters.bet_dwi = bet_dwi
    parameters.bet_mag = bet_mag
    parameters.total_readout = total_readout
    parameters.ignore_nodes = ignore_nodes
    parameters.analysis_level = analysis_level
    parameters.synb0_dir = synb0_dir
    parameters.acqp_file = acqp_file

    wf = init_dmripreproc_wf(parameters)
    wf.write_graph(graph2use="colored")
    wf.config["execution"]["remove_unnecessary_outputs"] = False
    wf.config["execution"]["keep_inputs"] = True
    wf.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
