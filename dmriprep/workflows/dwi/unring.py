# -*- coding: utf-8 -*-

from nipype.pipeline import engine as pe
from nipype.interfaces import mrtrix3, utility as niu


def init_unring_wf():

    wf = pe.Workflow(name="unring_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(fields=["dwi_file"]), name="inputnode"
    )

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["out_file"]), name="outputnode"
    )

    unring = pe.Node(mrtrix3.MRDeGibbs(), name="unring")

    wf.connect(
        [
            (inputnode, unring, [("dwi_file", "in_file")]),
            (unring, outputnode, [("out_file", "out_file")]),
        ]
    )

    return wf
