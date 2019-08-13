# -*- coding: utf-8 -*-

from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, utility as niu


def init_tensor_wf():

    wf = pe.Workflow(name="tensor_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["dwi_file", "bvec_file", "bval_file", "mask_file"]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["FA_file", "MD_file", "AD_file", "RD_file", "sse_file", "V1_file"]
        ),
        name="outputnode",
    )

    dtifit = pe.Node(fsl.DTIFit(save_tensor=True, sse=True), name="dtifit")

    add_l2_l3 = pe.Node(fsl.BinaryMaths(operation="add"), name="add_l2_l3")

    calc_rd = pe.Node(fsl.BinaryMaths(operand_value=2, operation="div"), name="calc_rd")

    wf.connect(
        [
            (
                inputnode,
                dtifit,
                [
                    ("dwi_file", "dwi"),
                    ("bvec_file", "bvecs"),
                    ("bval_file", "bvals"),
                    ("mask_file", "mask"),
                ],
            ),
            (dtifit, add_l2_l3, [("L2", "in_file"), ("L3", "operand_file")]),
            (add_l2_l3, calc_rd, [("out_file", "in_file")]),
            (calc_rd, outputnode, [("out_file", "RD_file")]),
            (
                dtifit,
                outputnode,
                [
                    ("FA", "FA_file"),
                    ("MD", "MD_file"),
                    ("L1", "AD_file"),
                    ("sse", "sse_file"),
                    ("V1", "V1_file"),
                ],
            ),
        ]
    )

    return wf
