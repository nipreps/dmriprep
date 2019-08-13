# -*- coding: utf-8 -*-

"""
Denoising, unringing and resampling of dwi images
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import mrtrix3, utility as niu


def init_prep_dwi_wf(ignore, output_resolution):

    prep_dwi_wf = pe.Workflow(name="prep_dwi_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_file"]), name="inputnode")

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_file"]), name="outputnode")

    denoise = pe.Node(mrtrix3.DWIDenoise(), name="denoise")

    unring = pe.Node(mrtrix3.MRDeGibbs(), name="unring")

    resample = pe.Node(mrtrix3.MRResize(voxel_size=output_resolution), name="resample")

    prep_full = ["denoise", "unring", "resample"]

    if not output_resolution:
        ignore.append("resample")

    prep_wanted_str = [node for node in prep_full if not (node in ignore)]

    # Translate string input to node names
    str2node = {"denoise": denoise, "unring": unring, "resample": resample}

    prep_wanted = [str2node[str_node] for str_node in prep_wanted_str]

    # If no steps selected, just connect input to output
    if not (prep_wanted):
        prep_dwi_wf.connect([(inputnode, outputnode, [("dwi_file", "out_file")])])

    # If there are steps
    else:
        # Must at least connect input node to first node
        first_node = prep_wanted[0]
        prep_dwi_wf.connect([(inputnode, first_node, [("dwi_file", "in_file")])])
        # Loop through the prep order
        # Note: only works if each node has in_file and out_file
        # Can work around this by wrapping in node/workflow with in_file+out_file
        prev = first_node
        for curr_node in prep_wanted[1:]:
            prep_dwi_wf.connect([(prev, curr_node, [("out_file", "in_file")])])
            prev = curr_node
        # Connect last node to output node
        last_node = prep_wanted[-1]
        prep_dwi_wf.connect([(last_node, outputnode, [("out_file", "out_file")])])

    return prep_dwi_wf
