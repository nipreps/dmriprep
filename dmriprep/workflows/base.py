"""dMRIPrep base processing workflows."""
from .. import config
import sys
import os
from copy import deepcopy

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from niworkflows.interfaces.bids import (
    BIDSInfo, BIDSFreeSurferDir
)
from niworkflows.utils.misc import fix_multi_T1w_source_name
from niworkflows.utils.spaces import Reference
from smriprep.workflows.anatomical import init_anat_preproc_wf

from ..interfaces import DerivativesDataSink, BIDSDataGrabber
from ..interfaces.reports import SubjectSummary, AboutSummary
from ..utils.bids import collect_data
from .dwi.base import init_early_b0ref_wf
from .fmap.base import init_fmap_estimation_wf


def init_dmriprep_wf():
    """
    Create the base workflow.

    This workflow organizes the execution of *dMRIPrep*, with a sub-workflow for
    each subject. If FreeSurfer's recon-all is to be run, a FreeSurfer derivatives folder is
    created and populated with any needed template subjects.

    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes

            from dmriprep.config.testing import mock_config
            from dmriprep.workflows.base import init_dmriprep_wf
            with mock_config():
                wf = init_dmriprep_wf()

    """
    dmriprep_wf = Workflow(name="dmriprep_wf")
    dmriprep_wf.base_dir = config.execution.work_dir

    freesurfer = config.workflow.run_reconall
    if freesurfer:
        fsdir = pe.Node(
            BIDSFreeSurferDir(
                derivatives=config.execution.output_dir,
                freesurfer_home=os.getenv("FREESURFER_HOME"),
                spaces=config.workflow.spaces.get_fs_spaces()),
            name=f"fsdir_run_{config.execution.run_uuid.replace('-', '_')}",
            run_without_submitting=True)
        if config.execution.fs_subjects_dir is not None:
            fsdir.inputs.subjects_dir = str(config.execution.fs_subjects_dir.absolute())

    for subject_id in config.execution.participant_label:
        single_subject_wf = init_single_subject_wf(subject_id)

        single_subject_wf.config["execution"]["crashdump_dir"] = str(
            config.execution.output_dir / "dmriprep" / f"sub-{subject_id}"
            / "log" / config.execution.run_uuid
        )

        for node in single_subject_wf._get_all_nodes():
            node.config = deepcopy(single_subject_wf.config)
        if freesurfer:
            dmriprep_wf.connect(fsdir, "subjects_dir",
                                single_subject_wf, "fsinputnode.subjects_dir")
        else:
            dmriprep_wf.add_nodes([single_subject_wf])

        # Dump a copy of the config file into the log directory
        log_dir = config.execution.output_dir / "dmriprep" / f"sub-{subject_id}" \
            / "log" / config.execution.run_uuid
        log_dir.mkdir(exist_ok=True, parents=True)
        config.to_filename(log_dir / "dmriprep.toml")

    return dmriprep_wf


def init_single_subject_wf(subject_id):
    """
    Set-up the preprocessing pipeline for a single subject.

    It collects and reports information about the subject, and prepares
    sub-workflows to perform anatomical and diffusion MRI preprocessing.

    Anatomical preprocessing is performed in a single workflow, regardless of
    the number of sessions.
    Diffusion MRI preprocessing is performed using a separate workflow for
    a full :abbr:`DWI (diffusion weighted imaging)` *entity*.
    A DWI *entity* may comprehend one or several runs (for instance, two
    opposed :abbr:`PE (phase-encoding)` directions.

    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes

            from dmriprep.config.testing import mock_config
            from dmriprep.workflows.base import init_single_subject_wf
            with mock_config():
                wf = init_single_subject_wf("THP0005")

    Parameters
    ----------
    subject_id : str
        List of subject labels

    Inputs
    ------
    subjects_dir : os.pathlike
        FreeSurfer's ``$SUBJECTS_DIR``

    """
    name = f"single_subject_{subject_id}_wf"
    subject_data = collect_data(
        config.execution.layout,
        subject_id)[0]

    if "flair" in config.workflow.ignore:
        subject_data["flair"] = []
    if "t2w" in config.workflow.ignore:
        subject_data["t2w"] = []

    anat_only = config.workflow.anat_only

    # Make sure we always go through these two checks
    if not anat_only and not subject_data["dwi"]:
        raise Exception(f"No DWI data found for participant {subject_id}. "
                        "All workflows require DWI images.")

    if not subject_data["t1w"]:
        raise Exception(f"No T1w images found for participant {subject_id}. "
                        "All workflows require T1w images.")

    workflow = Workflow(name=name)
    workflow.__desc__ = f"""
Results included in this manuscript come from preprocessing
performed using *dMRIPrep* {config.environment.version}
(@dmriprep; RRID:SCR_017412),
which is based on *Nipype* {config.environment.nipype_version}
(@nipype1; @nipype2; RRID:SCR_002502).

"""
    workflow.__postdesc__ = """

For more details of the pipeline, see [the section corresponding
to workflows in *dMRIPrep*'s documentation]\
(https://nipreps.github.io/dmriprep/master/workflows.html \
"dMRIPrep's documentation").


### Copyright Waiver

The above boilerplate text was automatically generated by dMRIPrep
with the express intention that users should copy and paste this
text into their manuscripts *unchanged*.
It is released under the [CC0]\
(https://creativecommons.org/publicdomain/zero/1.0/) license.

### References

"""
    spaces = config.workflow.spaces
    output_dir = config.execution.output_dir

    fsinputnode = pe.Node(niu.IdentityInterface(fields=["subjects_dir"]),
                          name="fsinputnode")

    bidssrc = pe.Node(BIDSDataGrabber(subject_data=subject_data, anat_only=anat_only),
                      name="bidssrc")

    bids_info = pe.Node(BIDSInfo(
        bids_dir=config.execution.bids_dir, bids_validate=False), name="bids_info")

    summary = pe.Node(SubjectSummary(std_spaces=spaces.get_spaces(nonstandard=False),
                                     nstd_spaces=spaces.get_spaces(standard=False)),
                      name="summary", run_without_submitting=True)

    about = pe.Node(AboutSummary(version=config.environment.version,
                                 command=" ".join(sys.argv)),
                    name="about", run_without_submitting=True)

    ds_report_summary = pe.Node(
        DerivativesDataSink(base_directory=str(output_dir), desc="summary", datatype="figures"),
        name="ds_report_summary", run_without_submitting=True)

    ds_report_about = pe.Node(
        DerivativesDataSink(base_directory=str(output_dir), desc="about", datatype="figures"),
        name="ds_report_about", run_without_submitting=True)

    anat_derivatives = config.execution.anat_derivatives
    if anat_derivatives:
        from smriprep.utils.bids import collect_derivatives
        std_spaces = spaces.get_spaces(nonstandard=False, dim=(3,))
        anat_derivatives = collect_derivatives(
            anat_derivatives.absolute(),
            subject_id,
            std_spaces,
            config.workflow.run_reconall,
        )

    # Preprocessing of T1w (includes registration to MNI)
    anat_preproc_wf = init_anat_preproc_wf(
        bids_root=str(config.execution.bids_dir),
        debug=config.execution.debug is True,
        existing_derivatives=anat_derivatives,
        freesurfer=config.workflow.run_reconall,
        hires=config.workflow.hires,
        longitudinal=config.workflow.longitudinal,
        omp_nthreads=config.nipype.omp_nthreads,
        output_dir=str(output_dir),
        skull_strip_fixed_seed=config.workflow.skull_strip_fixed_seed,
        skull_strip_mode="force",
        skull_strip_template=Reference.from_string(
            config.workflow.skull_strip_template)[0],
        spaces=spaces,
        t1w=subject_data["t1w"],
    )

    workflow.connect([
        (fsinputnode, anat_preproc_wf, [("subjects_dir", "inputnode.subjects_dir")]),
        (bidssrc, bids_info, [(("t1w", fix_multi_T1w_source_name), "in_file")]),
        (fsinputnode, summary, [("subjects_dir", "subjects_dir")]),
        (bidssrc, summary, [("t1w", "t1w"),
                            ("t2w", "t2w"),
                            ("dwi", "dwi")]),
        (bids_info, summary, [("subject", "subject_id")]),
        (bids_info, anat_preproc_wf, [(("subject", _prefix), "inputnode.subject_id")]),
        (bidssrc, anat_preproc_wf, [("t1w", "inputnode.t1w"),
                                    ("t2w", "inputnode.t2w"),
                                    ("roi", "inputnode.roi"),
                                    ("flair", "inputnode.flair")]),
        (bidssrc, ds_report_summary, [(("t1w", fix_multi_T1w_source_name), "source_file")]),
        (summary, ds_report_summary, [("out_report", "in_file")]),
        (bidssrc, ds_report_about, [(("t1w", fix_multi_T1w_source_name), "source_file")]),
        (about, ds_report_about, [("out_report", "in_file")]),
    ])

    # Overwrite ``out_path_base`` of smriprep's DataSinks
    for node in workflow.list_node_names():
        if node.split(".")[-1].startswith("ds_"):
            workflow.get_node(node).interface.out_path_base = "dmriprep"

    if anat_only:
        return workflow

    # Append the dMRI section to the existing anatomical excerpt
    # That way we do not need to stream down the number of bold datasets
    anat_preproc_wf.__postdesc__ = (anat_preproc_wf.__postdesc__ or "") + f"""
Diffusion data preprocessing

: For each of the {len(subject_data["dwi"])} DWI scans found per subject
 (across all sessions), the gradient table was vetted and converted into the *RASb*
format (i.e., given in RAS+ scanner coordinates, normalized b-vectors and scaled b-values),
and a *b=0* average for reference to the subsequent steps of preprocessing was calculated.
"""

    layout = config.execution.layout
    dwi_data = tuple([
        (dwi, layout.get_metadata(dwi), layout.get_bvec(dwi), layout.get_bval(dwi))
        for dwi in subject_data["dwi"]
    ])

    inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_data"]),
                        name="inputnode")
    inputnode.iterables = [("dwi_data", dwi_data)]

    referencenode = pe.JoinNode(niu.IdentityInterface(
        fields=["dwi_file", "metadata", "dwi_reference", "dwi_mask", "gradients_rasb"]),
        name="referencenode", joinsource="inputnode", run_without_submitting=True)

    split_info = pe.Node(niu.Function(
        function=_unpack, output_names=["dwi_file", "metadata", "bvec", "bval"]),
        name="split_info", run_without_submitting=True)

    early_b0ref_wf = init_early_b0ref_wf()
    workflow.connect([
        (inputnode, split_info, [("dwi_data", "in_tuple")]),
        (split_info, early_b0ref_wf, [("dwi_file", "inputnode.dwi_file"),
                                      ("bvec", "inputnode.in_bvec"),
                                      ("bval", "inputnode.in_bval")]),
        (split_info, referencenode, [("dwi_file", "dwi_file"),
                                     ("metadata", "metadata")]),
        (early_b0ref_wf, referencenode, [
            ("outputnode.dwi_reference", "dwi_reference"),
            ("outputnode.dwi_mask", "dwi_mask"),
            ("outputnode.gradients_rasb", "gradients_rasb"),
        ]),
    ])

    fmap_estimation_wf = init_fmap_estimation_wf(
        subject_data["dwi"], debug=config.execution.debug)
    workflow.connect([
        (referencenode, fmap_estimation_wf, [
            ("dwi_reference", "inputnode.dwi_reference"),
            ("dwi_mask", "inputnode.dwi_mask")]),
    ])
    return workflow


def _prefix(subid):
    return "-".join(("sub", subid.lstrip("sub-")))


def _unpack(in_tuple):
    return in_tuple
