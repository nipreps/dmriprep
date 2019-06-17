# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
.. _sdc_direct_b0 :
Direct B0 mapping sequences
~~~~~~~~~~~~~~~~~~~~~~~~~~~
When the fieldmap is directly measured with a prescribed sequence (such as
:abbr:`SE (spiral echo)`), we only need to calculate the corresponding B-Spline
coefficients to adapt the fieldmap to the TOPUP tool.
This procedure is described with more detail `here <https://cni.stanford.edu/\
wiki/GE_Processing#Fieldmaps>`__.
This corresponds to the section 8.9.3 --fieldmap image (and one magnitude image)--
of the BIDS specification.
"""
# from sdcflows.workflows.fmap import init_fmap_wf
#
# __all__ = ["init_fmap_wf"]


def init_fmap_wf():
    from nipype.pipeline import engine as pe
    from nipype.interfaces import fsl, utility as niu
    from nipype import logging

    fmap_wf = pe.Workflow(name="fmap_prep_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(fields=["fieldmap", "magnitude", "b0_stripped"]),
        name="inputnode",
    )

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_fmap"]), name="outputnode")

    rad_to_hz = pe.Node(
        fsl.BinaryMaths(operation="div", operand_value=6.28), name="radToHz"
    )

    mag_flirt = pe.Node(fsl.FLIRT(), name="magFlirt")

    fmap_flirt = pe.Node(fsl.FLIRT(apply_xfm=True), name="fmapFlirt")

    fmap_wf.connect(
        [
            (inputnode, rad_to_hz, [("fieldmap", "in_file")]),
            (inputnode, mag_flirt, [("magnitude", "in_file")]),
            (inputnode, mag_flirt, [("b0_stripped", "reference")]),
            (rad_to_hz, fmap_flirt, [("out_file", "in_file")]),
            (inputnode, fmap_flirt, [("b0_stripped", "reference")]),
            (mag_flirt, fmap_flirt, [("out_matrix_file", "in_matrix_file")]),
            (fmap_flirt, outputnode, [("out_file", "out_fmap")]),
        ]
    )

    return fmap_wf
