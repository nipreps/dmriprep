#!/usr/bin/env python

def init_dwiprep_wf(ignore_nodes):
    from ...interfaces import mrtrix3
    from nipype.pipeline import engine as pe
    from nipype.interfaces import fsl, utility as niu

    # Generate the prep workflow for dwi (denoise, unring, resize)

    dwi_prep_wf = pe.Workflow(name="dwi_prep_wf")

    denoise = pe.Node(mrtrix3.DWIDenoise(), name="denoise")

    unring = pe.Node(mrtrix3.MRDeGibbs(), name="unring")

    resize = pe.Node(mrtrix3.MRResize(voxel_size=[1]), name="resize")

    dwi_prep_inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["dwi_file"]
        ),
        name="dwi_prep_inputnode",
    )

    dwi_prep_outputnode = pe.Node(
        niu.IdentityInterface(fields=["out_file"]),
        name="dwi_prep_outputnode",
    )

    # Turn the string input of nodes into a list
    ignore_nodes_list = [option.lower() for option in ignore_nodes.strip()]

    prep_full = ['d', 'u', 'r']
    prep_wanted_str = [node for node in prep_full if not(node in ignore_nodes_list)]

    # Translate string input to node names
    str2node = {
        'd': denoise,
        'u': unring,
        'r': resize
    }

    # Convert the string list to a node list
    prep_wanted = [str2node[str_node] for str_node in prep_wanted_str]

    # If no steps selected, just connect input to output
    if not(prep_wanted):
        dwi_prep_wf.connect(
            [
                (dwi_prep_inputnode, dwi_prep_outputnode, [("dwi_file", "out_file")])
            ]
        )

    # If there are steps
    else:
        # Must at least connect input node to first node
        first_node = prep_wanted[0]
        dwi_prep_wf.connect(
            [
                (dwi_prep_inputnode, first_node, [("dwi_file", "in_file")]),
            ]
        )
        # Loop through the prep order
        # Note: only works if each node has in_file and out_file
        # Can work around this by wrapping in node/workflow with in_file+out_file
        prev = first_node
        for curr_node in prep_wanted[1:]:
            dwi_prep_wf.connect(
                [
                    (prev, curr_node, [("out_file", "in_file")]),
                ]
            )
            prev = curr_node
        # Connect last node to output node
        last_node = prep_wanted[-1]
        dwi_prep_wf.connect(
            [
                (last_node, dwi_prep_outputnode, [("out_file", "out_file")]),
            ]
        )

    return dwi_prep_wf
