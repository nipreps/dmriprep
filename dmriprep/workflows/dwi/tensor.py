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
        niu.IdentityInterface(fields=["FA_file", "V1_file", "sse_file"]),
        name="outputnode",
    )

    dtifit = pe.Node(fsl.DTIFit(save_tensor=True, sse=True), name="dtifit")

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
            (
                dtifit,
                outputnode,
                [("FA", "FA_file"), ("V1", "V1_file"), ("sse", "sse_file")],
            ),
        ]
    )

    return wf
