# -*- coding: utf-8 -*-

"""
Artefact removal and resizing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_artifacts_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu

from dmriprep.due import due, BibTeX
from dmriprep.interfaces import mrtrix3


@due.dcite(BibTeX(
    """
    @article{denoise1,
    title = {Denoising of diffusion MRI using random matrix theory},
    volume = {142},
    doi = {10.1016/j.neuroimage.2016.08.016},
    journal = {NeuroImage},
    author = {Veraart, J.; Novikov, D.S.; Christiaens, D.; Ades-aron, B.; Sijbers, J. & Fieremans, E.},
    year = {2016},
    pages = {394-406}}
    """),
    description='Denoising algorithm')
@due.dcite(BibTeX(
    """
    @article{denoise2,
    title = {Diffusion MRI noise mapping using random matrix theory},
    volume = {76},
    doi = {10.1002/mrm.26059},
    journal = {Magnetic Resonance in Medicine},
    author = {Veraart, J.; Fieremans, E. & Novikov, D.S.},
    year = {2016},
    pages = {1582-1593}}
    """),
    description='Denoising algorithm')
@due.dcite(BibTeX(
    """
    @article{unring,
    title = {Gibbs-ringing artifact removal based on local subvoxel-shifts},
    volume = {76},
    doi = {10.1002/mrm.26054},
    journal = {Magnetic Resonance in Medicine},
    author = {Kellner, E; Dhital, B; Kiselev, V.G & Reisert, M.},
    year = {2016},
    pages = {1574–1581}}
    """),
    description='Unringing algorithm')
def init_dwi_artifacts_wf(ignore, output_resolution):
    """
    This workflow performs denoising and unringing on the input dwi image.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.dwi import init_dwi_artifacts_wf
        wf = init_dwi_artifacts_wf(ignore=[], output_resolution=(1, 1, 1))

    **Parameters**

        ignore : :obj:`list`
            List of artefact removal steps to skip (default: [])

    **Inputs**

        dwi_file : :obj:`str`
            dwi NIfTI file

    **Outputs**

        out_file : :obj:`str`
            dwi NIfTI file after artefact removal

    """

    wf = pe.Workflow(name='dwi_artifacts_wf')

    inputnode = pe.Node(niu.IdentityInterface(fields=['dwi_file']), name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file']), name='outputnode')

    dwibuffer = pe.Node(niu.IdentityInterface(fields=['dwi_file']), name='dwibuffer')

    denoise = pe.Node(mrtrix3.DWIDenoise(), name='denoise')

    unring = pe.Node(mrtrix3.MRDeGibbs(), name='unring')

    resize = pe.Node(mrtrix3.MRResize(), name='resize')

    if ignore == ['denoising']:
        wf.connect([
            (inputnode, unring, [('dwi_file', 'in_file')]),
            (unring, dwibuffer, [('out_file', 'dwi_file')])
        ])

    elif ignore == ['unringing']:
        wf.connect([
            (inputnode, denoise, [('dwi_file', 'in_file')]),
            (denoise, dwibuffer, [('out_file', 'dwi_file')])
        ])

    elif ['denoising', 'unringing'] in ignore:
        wf.connect([
            (inputnode, dwibuffer, 'dwi_file', 'dwi_file')
        ])

    else:
        wf.connect([
            (inputnode, denoise, [('dwi_file', 'in_file')]),
            (denoise, unring, [('out_file', 'in_file')]),
            (unring, dwibuffer, [('out_file', 'dwi_file')])
        ])

    if output_resolution:
        resize.inputs.voxel_size = output_resolution
        wf.connect([
            (dwibuffer, resize, [('dwi_file', 'in_file')]),
            (resize, outputnode, [('out_file', 'out_file')])
        ])

    else:
        wf.connect([
            (dwibuffer, outputnode, [('dwi_file', 'out_file')])
        ])

    return wf
