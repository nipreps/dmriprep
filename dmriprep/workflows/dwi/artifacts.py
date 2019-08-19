# -*- coding: utf-8 -*-

"""
Artefact removal
^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_artifacts_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import mrtrix3, utility as niu


def init_dwi_artifacts_wf(ignore):
    """
    This workflow performs denoising and unringing on the input dwi image.

    Denoising is done using Mrtrix3's implementation of the MP-PCA
    algorithm `[Veraart2016a_]` and `[Veraart2016b_]`.
    Unringing is done using Mrtrix3  `[Kellner2016_]`.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.dwi import init_dwi_artifacts_wf
        wf = init_dwi_artifacts_wf(ignore=[])

    **Parameters**

        ignore : list
            List of artefact removal steps to skip (default: [])

    **Inputs**

        dwi_file
            dwi NIfTI file

    **Outputs**

        out_file
            dwi NIfTI file after artefact removal

    References
    ^^^^^^^^^^

    .. [Veraart2016a] Veraart, J.; Novikov, D.S.; Christiaens, D.; Ades-aron, B.;
                      Sijbers, J. & Fieremans, E. Denoising of diffusion MRI
                      using random matrix theory. NeuroImage, 2016, 142, 394-406,
                      doi: `10.1016/j.neuroimage.2016.08.016 <https://doi.org/10.1016/j.neuroimage.2016.08.016>`_.

    .. [Veraart2016b] Veraart, J.; Fieremans, E. & Novikov, D.S. Diffusion MRI
                      noise mapping using random matrix theory. Magn. Res. Med.,
                      2016, 76(5), 1582-1593,
                      doi: `10.1002/mrm.26059 <https://doi.org/10.1002/mrm.26059>`_.

    .. [Kellner2016] Kellner, E; Dhital, B; Kiselev, V.G & Reisert, M.
                     Gibbs-ringing artifact removal based on local subvoxel-shifts.
                     Magnetic Resonance in Medicine, 2016, 76, 1574–1581,
                     doi: `10.1002/mrm.26054 <https://doi.org/10.1002/mrm.26054>`_.

    """

    wf = pe.Workflow(name="dwi_artifacts_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_file"]), name="inputnode")

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_file"]), name="outputnode")

    denoise = pe.Node(mrtrix3.DWIDenoise(), name="denoise")

    unring = pe.Node(mrtrix3.MRDeGibbs(), name="unring")

    if ignore == ["denoise"]:
        wf.connect([
            (inputnode, unring, [("dwi_file", "in_file")]),
            (unring, outputnode, [("out_file", "out_file")])
        ])

    elif ignore == ["unring"]:
        wf.connect([
            (inputnode, denoise, [("dwi_file", "in_file")]),
            (denoise, outputnode, [("out_file", "out_file")])
        ])

    elif ["denoise", "unring"] in ignore:
        wf.connect([
            (inputnode, outputnode, "dwi_file", "out_file")
        ])

    else:
        wf.connect([
            (inputnode, denoise, [("dwi_file", "in_file")]),
            (denoise, unring, [("out_file", "in_file")]),
            (unring, outputnode, [("out_file", "out_file")])
        ])

    return wf
