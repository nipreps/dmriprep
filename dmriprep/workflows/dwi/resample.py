# -*- coding: utf-8 -*-

from nipype.pipeline import engine as pe
from nipype.interfaces import mrtrix3, utility as niu


def init_resample_wf():

    wf = pe.Workflow(name="resample_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(fields=["dwi_file"]), name="inputnode"
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["out_file"]), name="outputnode"
    )

    resample = pe.Node(mrtrix3.MRResize(), name="resample")

    wf.connect(
        [
            (inputnode, unring, [("dwi_file", "in_file")]),
            (unring, outputnode, [("out_file", "out_file")]),
        ]
    )

    return wf
