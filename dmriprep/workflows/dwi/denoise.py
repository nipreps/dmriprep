# -*- coding: utf-8 -*-

from nipype.pipeline import engine as pe
from nipype.interfaces import mrtrix3, utility as niu


def init_denoise_wf():

    wf = pe.Workflow(name="denoise_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_file"]), name="inputnode")

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_file"]), name="outputnode")

    denoise = pe.Node(mrtrix3.DWIDenoise(), name="denoise")

    wf.connect(
        [
            (inputnode, denoise, [("dwi_file", "in_file")]),
            (denoise, outputnode, [("out_file", "out_file")]),
        ]
    )

    return wf
