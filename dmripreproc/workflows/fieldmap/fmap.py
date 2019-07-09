#!/usr/bin/env python

from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, utility as niu


def init_fmap_wf():

    wf = pe.Workflow(name="fmap_prep_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(fields=["fieldmap", "magnitude", "b0_stripped"]),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["out_fmap"]), name="outputnode"
    )

    rad_to_hz = pe.Node(
        fsl.BinaryMaths(operation="div", operand_value=6.28), name="radToHz"
    )

    mag_flirt = pe.Node(fsl.FLIRT(dof=6), name="magFlirt")

    fmap_flirt = pe.Node(fsl.FLIRT(apply_xfm=True), name="fmapFlirt")

    wf.connect(
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

    return wf
