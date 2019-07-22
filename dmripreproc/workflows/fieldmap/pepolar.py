#!/usr/bin/env python

from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, utility as niu


def init_pepolar_wf(subject_id, dwi_meta, epi_fmaps):

    dwi_file_pe = dwi_meta["PhaseEncodingDirection"]

    file2dir = dict()

    usable_fieldmaps_matching_pe = []
    usable_fieldmaps_opposite_pe = []

    for fmap, pe_dir in epi_fmaps:
        if pe_dir == dwi_file_pe:
            usable_fieldmaps_matching_pe.append(fmap)
            file2dir[fmap] = pe_dir
        elif pe_dir[0] == dwi_file_pe[0]:
            usable_fieldmaps_opposite_pe.append(fmap)
            file2dir[fmap] = pe_dir

    if not usable_fieldmaps_opposite_pe:
        raise Exception("None of the discovered fieldmaps for "
                        "participant {} has the right phase "
                        "encoding direction".format(subject_id))

    wf = pe.Workflow(name="pepolar_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["b0_stripped"]), name = "inputnode")

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_topup", "out_movpar", "out_fmap", "out_enc_file"]), name = "outputnode")

    topup_wf = init_topup_wf()
    topup_wf.inputs.inputnode.altepi_file = usable_fieldmaps_opposite_pe[0]
    wf.add_nodes([inputnode])

    if not usable_fieldmaps_matching_pe:
        wf.connect(
            [
                (inputnode, topup_wf, [("b0_stripped", "inputnode.epi_file")])
            ]
        )
    else:
        topup_wf.inputs.inputnode.epi_file = usable_fieldmaps_matching_pe[0]

    epi_list = [topup_wf.inputs.inputnode.epi_file, topup_wf.inputs.inputnode.altepi_file]
    dir_map = {
        'i': 'x',
        'i-': 'x-',
        'j': 'y',
        'j-': 'y-',
        'k': 'z',
        'k-': 'z-'
    }
    topup_wf.inputs.inputnode.encoding_directions = [dir_map[file2dir[file]] for file in epi_list]

    wf.connect(
        [
            (
                topup_wf,
                outputnode,
                [
                    ("outputnode.out_fmap", "out_fmap"),
                    ("outputnode.out_movpar", "out_movpar"),
                    ("outputnode.out_base", "out_topup"),
                    ("outputnode.out_enc_file", "out_enc_file"),
                ]
            ),
        ]
    )

    return wf

def init_synb0_wf(subject_id, dwi_meta, synb0):
    dwi_file_pe = dwi_meta["PhaseEncodingDirection"]

    file2dir = dict()

    usable_fieldmaps_matching_pe = []
    usable_fieldmaps_opposite_pe = []

    wf = pe.Workflow(name="synb0_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["b0_stripped"]), name = "inputnode")

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_topup", "out_movpar", "out_fmap", "out_enc_file"]), name = "outputnode")

    topup_wf = init_topup_wf(use_acqp=True)
    topup_wf.inputs.inputnode.altepi_file = synb0
    wf.add_nodes([inputnode])
    wf.connect(
        [
            (inputnode, topup_wf, [("b0_stripped", "inputnode.epi_file")])
        ]
    )
    topup_wf.inputs.inputnode.acqp = '/scratch/smansour/synb0_acqp.txt'

    wf.connect(
        [
            (
                topup_wf,
                outputnode,
                [
                    ("outputnode.out_fmap", "out_fmap"),
                    ("outputnode.out_movpar", "out_movpar"),
                    ("outputnode.out_base", "out_topup"),
                ]
            ),
        ]
    )

    return wf

def init_topup_wf(use_acqp=False):
    from ...interfaces import mrtrix3

    wf = pe.Workflow(name="topup_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(fields=["epi_file", "altepi_file", "encoding_directions", "topup_name", "acqp"]),
        name="inputnode")
    inputnode.inputs.topup_name = "topup_base"

    epi_flirt = pe.Node(fsl.FLIRT(), name="epi_flirt")

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["out_fmap", "out_movpar", "out_base", "out_enc_file"]),
        name="outputnode")

    list_merge = pe.Node(niu.Merge(numinputs=2), name="list_merge")

    merge = pe.Node(fsl.Merge(dimension="t"), name="mergeAPPA")

    # Resize (make optional)
    resize = pe.Node(mrtrix3.MRResize(voxel_size=[1]), name="epi_resize")

    topup = pe.Node(fsl.TOPUP(), name="topup")

    get_base_movpar = lambda x: x.split("_movpar.txt")[0]

    if use_acqp:
        wf.connect(
            [
                (inputnode, topup, [("acqp", "encoding_file")])
            ]
        )
    else:
        topup.inputs.readout_times = [0.05, 0.05]
        wf.connect(
            [
                (inputnode, topup, [("encoding_directions", "encoding_direction")])
            ]
        )

    wf.connect(
        [
            (
                inputnode,
                list_merge,
                [("epi_file", "in1")]
            ),
            (
                inputnode,
                epi_flirt,
                [("altepi_file", "in_file"), ("epi_file", "reference")]
            ),
            (epi_flirt, list_merge, [("out_file", "in2")]),
            (list_merge, merge, [("out", "in_files")]),
            (merge, resize, [("merged_file", "in_file")]),
            (resize, topup, [("out_file", "in_file")]),
            (
                topup,
                outputnode,
                [
                    ("out_field", "out_fmap"),
                    ("out_movpar", "out_movpar"),
                    ("out_enc_file", "out_enc_file"),
                    (("out_movpar", get_base_movpar), "out_base")
                ]
            ),
        ]
    )

    return wf
