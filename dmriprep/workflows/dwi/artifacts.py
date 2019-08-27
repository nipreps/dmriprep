# -*- coding: utf-8 -*-

"""
Artefact removal and resizing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_artifacts_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import mrtrix3, utility as niu


def init_dwi_artifacts_wf(ignore, output_resolution):
    """
    This workflow performs denoising and unringing on the input dwi image.

    Denoising is done using Mrtrix3's implementation of the MP-PCA
    algorithm @denoise1 and @denoise2.
    Unringing is done using Mrtrix3 @unring.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.dwi import init_dwi_artifacts_wf
        wf = init_dwi_artifacts_wf(ignore=[], output_resolution=(1, 1, 1))

    **Parameters**

        ignore: list
            List of artefact removal steps to skip (default: [])

    **Inputs**

        dwi_file
            dwi NIfTI file

    **Outputs**

        out_file
            dwi NIfTI file after artefact removal

    """

    wf = pe.Workflow(name='dwi_artifacts_wf')

    inputnode = pe.Node(niu.IdentityInterface(fields=['dwi_file']), name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file']), name='outputnode')

    dwibuffer = pe.Node(niu.IdentityInterface(fields=['dwi_file']), name='dwibuffer')

    denoise = pe.Node(mrtrix3.DWIDenoise(), name='denoise')

    unring = pe.Node(mrtrix3.MRDeGibbs(), name='unring')

    resize = pe.Node(mrtrix3.MRResize(voxel_size=output_resolution), name='resize')

    if ignore == ['denoise']:
        wf.connect([
            (inputnode, unring, [('dwi_file', 'in_file')]),
            (unring, outputnode, [('out_file', 'out_file')])
        ])

    elif ignore == ['unring']:
        wf.connect([
            (inputnode, denoise, [('dwi_file', 'in_file')]),
            (denoise, outputnode, [('out_file', 'out_file')])
        ])

    elif ['denoise', 'unring'] in ignore:
        wf.connect([
            (inputnode, outputnode, 'dwi_file', 'out_file')
        ])

    else:
        wf.connect([
            (inputnode, denoise, [('dwi_file', 'in_file')]),
            (denoise, unring, [('out_file', 'in_file')]),
            (unring, outputnode, [('out_file', 'out_file')])
        ])

    return wf
