# -*- coding: utf-8 -*-

"""
Utility workflows
^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_resize_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import mrtrix3, utility as niu


def init_dwi_resize_wf(output_resolution):
    """
    This workflow performs resizes the input image to the desired output resolution.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.dwi import init_dwi_resize_wf
        wf = init_dwi_resize_wf(output_resolution=(1, 1, 1))

    **Parameters**

        output_resolution: tuple
            Tuple of voxel sizes (in mm) in the x, y and z axes

    **Inputs**

        in_file
            input NIfTI file

    **Outputs**

        out_file
            output NIfTI file after resizing
    """

    wf = pe.Workflow(name='dwi_resize_wf')

    inputnode = pe.Node(niu.IdentityInterface(fields=['in_file']), name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file']), name='outputnode')

    resize = pe.Node(mrtrix3.MRResize(voxel_size=output_resolution), name='resize')

    wf.connect([
        (inputnode, resize, [('in_file', 'in_file')]),
        (resize, outputnode, [('out_file', 'out_file')])
    ])

    return wf
