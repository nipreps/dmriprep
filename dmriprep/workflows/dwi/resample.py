# -*- coding: utf-8 -*-

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu

from ...interfaces import mrtrix3


def init_resample_wf(parameters):

    wf = pe.Workflow(name="resample_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_file"]), name="inputnode")

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_file"]), name="outputnode")

    resample = pe.Node(
        mrtrix3.MRResize(voxel_size=parameters.output_resolution), name="resample"
    )

    wf.connect(
        [
            (inputnode, resample, [("dwi_file", "in_file")]),
            (resample, outputnode, [("out_file", "out_file")]),
        ]
    )

    return wf
