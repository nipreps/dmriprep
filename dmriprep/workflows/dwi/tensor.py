# -*- coding: utf-8 -*-

"""
Tensor fitting
^^^^^^^^^^^^^^

.. autofunction:: init_dwi_tensor_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, utility as niu


def init_dwi_tensor_wf():
    """
    This workflow fits a tensor to the input dwi image.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.dwi import init_dwi_tensor_wf
        wf = init_dwi_tensor_wf()

    **Inputs**

        dwi_file
            dwi NIfTI file
        bvec_file
            bvec file
        bval_file
            bval file
        mask_file
            brain mask file

    **Outputs**

        FA_file
            FA
        MD_file
            MD
        AD_file
            AD
        RD_file
            RD
        V1_file
            V1
        sse_file
            diffusion tensor fit residuals

    """

    wf = pe.Workflow(name="dwi_tensor_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["dwi_file", "bvec_file", "bval_file", "mask_file"]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["FA_file", "MD_file", "AD_file", "RD_file", "V1_file", "sse_file"]
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
                    ("V1", "V1_file"),
                    ("sse", "sse_file"),
                ],
            ),
        ]
    )

    return wf
