#!/usr/bin/env python

from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, utility as niu
from ...interfaces import Phasediff2Fieldmap, Phases2Fieldmap


def init_phase_wf(bet_mag_frac):

    wf = pe.Workflow(name="phase_prep_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["magnitude1", "phasediff", "b0_stripped", "phases_meta"]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["out_fmap", "out_mag"]),
        name="outputnode",
    )

    phases2fmap = pe.Node(Phases2Fieldmap(), name="phases2fmap")

    mag_bet = pe.Node(fsl.BET(frac=bet_mag_frac, robust=True), name="mag_bet")

    prep_fmap = pe.Node(
        fsl.PrepareFieldmap(scanner="SIEMENS", nocheck=True), name="prep_fmap"
    )

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name="fslroi_phase")

    delta = pe.Node(
        niu.Function(
            input_names=["in_values"],
            output_names=["out_value"],
            function=delta_te,
        ),
        name="delta",
    )

    wf.connect(
        [
            # Mag bet
            (inputnode, mag_bet, [("magnitude1", "in_file")]),
            # phases -> phdiff
            (inputnode, phases2fmap, [("phases_meta", "metadatas")]),
            (inputnode, phases2fmap, [("phasediff", "phase_files")]),
            # phdiff delta_te
            (phases2fmap, delta, [("phasediff_metadata", "in_values")]),
            # prep fmap
            (mag_bet, prep_fmap, [("out_file", "in_magnitude")]),
            (phases2fmap, prep_fmap, [("out_file", "in_phase")]),
            (delta, prep_fmap, [("out_value", "delta_TE")]),
            # Remove second empty volume
            (prep_fmap, fslroi, [("out_fieldmap", "in_file")]),
            (fslroi, outputnode, [("roi_file", "out_fmap")]),
            (inputnode, outputnode, [("magnitude1", "out_mag")]),
        ]
    )

    return wf


def init_phdiff_wf(bet_mag_frac):

    wf = pe.Workflow(name="phdiff_prep_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["magnitude1", "phasediff", "b0_stripped", "phases_meta"]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["out_fmap", "out_mag"]),
        name="outputnode",
    )

    mag_bet = pe.Node(fsl.BET(frac=bet_mag_frac, robust=True), name="mag_bet")

    prep_fmap = pe.Node(
        fsl.PrepareFieldmap(scanner="SIEMENS"), name="prep_fmap"
    )

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name="fslroi_phase")

    delta = pe.Node(
        niu.Function(
            input_names=["in_values"],
            output_names=["out_value"],
            function=delta_te,
        ),
        name="delta",
    )

    # phdiff2fmap = pe.Node(Phasediff2Fieldmap(), name='phdiff2fmap')

    wf.connect(
        [
            # mag bet
            (inputnode, mag_bet, [("magnitude1", "in_file")]),
            # phdiff delta_te
            (inputnode, delta, [("phases_meta", "in_values")]),
            # prep fmap
            (mag_bet, prep_fmap, [("out_file", "in_magnitude")]),
            (inputnode, prep_fmap, [("phasediff", "in_phase")]),
            (delta, prep_fmap, [("out_value", "delta_TE")]),
            # Remove second empty volume
            (prep_fmap, fslroi, [("out_fieldmap", "in_file")]),
            # Output
            (fslroi, outputnode, [("roi_file", "out_fmap")]),
            (inputnode, outputnode, [("magnitude1", "out_mag")]),
        ]
    )
    return wf


def get_metadata(in_file, bids_dir):
    from bids import BIDSLayout

    layout = BIDSLayout(bids_dir, validate=False)
    out_dict = layout.get_metadata(in_file)
    return out_dict


def delta_te(in_values, te1=None, te2=None):
    """Read :math:`\Delta_\text{TE}` from BIDS metadata dict"""
    if isinstance(in_values, float):
        te2 = in_values
        te1 = 0.0

    if isinstance(in_values, dict):
        te1 = in_values.get("EchoTime1")
        te2 = in_values.get("EchoTime2")

        if not all((te1, te2)):
            te2 = in_values.get("EchoTimeDifference")
            te1 = 0

    if isinstance(in_values, list):
        te2, te1 = in_values
        if isinstance(te1, list):
            te1 = te1[1]
        if isinstance(te2, list):
            te2 = te2[1]

    # For convienience if both are missing we should give one error about them
    if te1 is None and te2 is None:
        raise RuntimeError(
            "EchoTime1 and EchoTime2 metadata fields not found. "
            "Please consult the BIDS specification."
        )
    if te1 is None:
        raise RuntimeError(
            "EchoTime1 metadata field not found. Please consult the BIDS specification."
        )
    if te2 is None:
        raise RuntimeError(
            "EchoTime2 metadata field not found. Please consult the BIDS specification."
        )

    return 1000 * abs(float(te2) - float(te1))
