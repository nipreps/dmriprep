"""Deploy a susceptibility-distortion estimation strategy."""
from ... import config
from pkg_resources import resource_filename as _pkg_fname
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from ...interfaces import DerivativesDataSink


def init_fmap_estimation_wf(
    epi_targets,
    debug=False,
    generate_report=True,
    name="fmap_estimation_wf",
):
    """
    Setup a fieldmap estimation strategy and write results to derivatives folder.

    Parameters
    ----------
    participant_label : :obj:`str`
        The particular subject for which the BIDS layout will be queried.
    epi_targets : :obj:`list` of :obj:`os.pathlike`
        A list of :abbr:`EPI (echo planar imaging)` scans that will be corrected for
        susceptibility distortions with the estimated fieldmaps.
    omp_nthreads : :obj:`int`
        Number of CPUs available to individual processes for multithreaded execution.
    debug : :obj:`bool`
        Whether fast (and less accurate) execution parameters should be used whenever available.
    name : :obj:`str`
        A unique workflow name to build Nipype's workflow hierarchy.

    """
    layout = config.execution.layout
    wf = Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_reference", "dwi_mask"]),
                        name="inputnode")
    wf.add_nodes([inputnode])  # TODO: remove when fully implemented
    # Create one outputnode with a port for each potential EPI target
    # outputnode = pe.Node(niu.IdentityInterface(fields=[_fname2outname(p) for p in epi_targets]),
    #                      name="outputnode")

    # Return identity transforms for all if fieldmaps are ignored
    if "fieldmaps" in config.workflow.ignore:
        return wf

    # Set-up PEPOLAR estimators only with EPIs under fmap/
    # fmap_epi = {f: layout.get_metadata(f)
    #             for f in layout.get(
    #                 subject=participant_label, datatype="fmap",
    #                 suffix="epi", extension=("nii", "nii.gz"))}

    metadata = [layout.get_metadata(p) for p in epi_targets]
    if any("TotalReadoutTime" not in m for m in metadata):
        return wf

    pedirs = [m.get("PhaseEncodingDirection", "unknown") for m in metadata]
    if len(set(pedirs) - set(("unknown",))) > 1:
        if "unknown" in pedirs or len(set(pe[0] for pe in set(pedirs))) > 1:
            raise NotImplementedError

        # Get EPI polarities and their metadata
        sdc_estimate_wf = init_pepolar_estimate_wf(debug=debug)
        sdc_estimate_wf.inputs.inputnode.metadata = metadata

        wf.connect([
            (inputnode, sdc_estimate_wf, [("dwi_reference", "inputnode.in_data")]),
        ])
        if generate_report:
            from sdcflows.interfaces.reportlets import FieldmapReportlet
            pepolar_report = pe.Node(FieldmapReportlet(reference_label="SDC'd B0"),
                                     name="pepolar_report")
            ds_report_pepolar = pe.Node(DerivativesDataSink(
                base_directory=str(config.execution.output_dir), datatype="figures",
                suffix="fieldmap", desc="pepolar", dismiss_entities=("acquisition", "dir")),
                name="ds_report_pepolar")
            ds_report_pepolar.inputs.source_file = epi_targets[0]
            wf.connect([
                (sdc_estimate_wf, pepolar_report, [
                    ("outputnode.fieldmap", "fieldmap"),
                    ("outputnode.corrected", "reference"),
                    ("outputnode.corrected_mask", "mask")]),
                (pepolar_report, ds_report_pepolar, [("out_report", "in_file")]),
            ])

    return wf


def init_pepolar_estimate_wf(debug=False, generate_report=True, name="pepolar_estimate_wf"):
    """Initialize a barebones TOPUP implementation."""
    from nipype.interfaces.afni import Automask
    from nipype.interfaces.fsl.epi import TOPUP
    from niworkflows.interfaces.nibabel import MergeSeries
    from sdcflows.interfaces.fmap import get_trt
    from ...interfaces.images import RescaleB0
    wf = Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(fields=["metadata", "in_data"]),
                        name="inputnode")
    outputnode = pe.Node(niu.IdentityInterface(fields=["fieldmap", "corrected", "corrected_mask"]),
                         name="outputnode")

    concat_blips = pe.Node(MergeSeries(), name="concat_blips")
    readout_time = pe.MapNode(niu.Function(
        input_names=["in_meta", "in_file"], function=get_trt), name="readout_time",
        iterfield=["in_meta", "in_file"], run_without_submitting=True
    )

    topup = pe.Node(TOPUP(config=_pkg_fname(
        "dmriprep", f"data/flirtsch/b02b0{'_quick' * debug}.cnf")), name="topup")

    pre_mask = pe.Node(Automask(dilate=1, outputtype="NIFTI_GZ"),
                       name="pre_mask")
    rescale_corrected = pe.Node(RescaleB0(), name="rescale_corrected")
    post_mask = pe.Node(Automask(outputtype="NIFTI_GZ"),
                        name="post_mask")
    wf.connect([
        (inputnode, concat_blips, [("in_data", "in_files")]),
        (inputnode, readout_time, [("in_data", "in_file"),
                                   ("metadata", "in_meta")]),
        (inputnode, topup, [(("metadata", _get_pedir), "encoding_direction")]),
        (readout_time, topup, [("out", "readout_times")]),
        (concat_blips, topup, [("out_file", "in_file")]),
        (topup, pre_mask, [("out_corrected", "in_file")]),
        (pre_mask, rescale_corrected, [("out_file", "mask_file")]),
        (topup, rescale_corrected, [("out_corrected", "in_file")]),
        (topup, outputnode, [("out_field", "fieldmap")]),
        (rescale_corrected, post_mask, [("out_ref", "in_file")]),
        (rescale_corrected, outputnode, [("out_ref", "corrected")]),
        (post_mask, outputnode, [("out_file", "corrected_mask")]),
    ])

    return wf


def _get_pedir(metadata):
    return [m["PhaseEncodingDirection"].replace("j", "y").replace("i", "x").replace("k", "z")
            for m in metadata]


# def _fname2outname(in_file):
#     from pathlib import Path
#     return Path(in_file).name.rstrip(".gz").rstrip(".nii").replace("-", "_")
