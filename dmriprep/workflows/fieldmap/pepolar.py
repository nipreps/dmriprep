#!/usr/bin/env python

from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, utility as niu


def init_pepolar_wf(subject_id, dwi_meta, epi_fmaps):

    dwi_file_pe = dwi_meta["PhaseEncodingDirection"]

    usable_fieldmaps_matching_pe = []
    usable_fieldmaps_opposite_pe = []

    for fmap, pe_dir in epi_fmaps:
        if pe_dir == dwi_file_pe:
            usable_fieldmaps_matching_pe.append(fmap)
        elif pe_dir[0] == dwi_file_pe[0]:
            usable_fieldmaps_opposite_pe.append(fmap)

    if not usable_fieldmaps_opposite_pe:
        raise Exception("None of the discovered fieldmaps for "
                        "participant {} has the right phase "
                        "encoding direction".format(subject_id))

    wf = pe.Workflow(name="pepolar_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["b0_stripped"]))

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_topup"]))

    topup_wf = init_topup_wf()
    topup_wf.inputnode.altepi_file = usable_fieldmaps_opposite_pe[0]

    if not usable_fieldmaps_matching_pe:
        wf.connect(
            [
                (inputnode, topup_wf, [("b0_stripped", "inputnode.epi_file")])
            ]
        )
    else:
        topup_wf.inputnode.epi_file = usable_fieldmaps_matching_pe[0]

    return wf


def init_topup_wf():

    wf = pe.Workflow(name="topup_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(fields=["epi_file", "altepi_file", "encoding_directions"]),
        name="inputnode")

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["out_fmap"]),
        name="outputnode")

    list_merge = pe.Node(niu.Merge(numinputs=2), name="list_merge")

    merge = pe.Node(fsl.Merge(dimension="t"), name="mergeAPPA")

    topup = pe.Node(fsl.TOPUP(), name="topup")
    topup.inputs.readout_times = [0.05, 0.05]

    wf.connect(
        [
            (
                inputnode,
                list_merge,
                [("epi_file", "in1"), ("altepi_file", "in2")]
            ),
            (list_merge, merge, [("out", "in_files")]),
            (merge, topup, [("merged_file", "in_file")]),
            (inputnode, topup, [("encoding_directions", "encoding_direction")]),
            (topup, outputnode, [("out_field", "out_fmap")]),
        ]
    )

    return wf
