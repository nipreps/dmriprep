# -*- coding: utf-8 -*-

"""
Utility workflows
^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_concat_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu


def init_dwi_concat_wf(layout):
    """
    This workflow concatenates a list of dwi images as well as their associated
    bvecs and bvals.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from collections import namedtuple
        from dmriprep.workflows.dwi import init_dwi_concat_wf
        BIDSLayout = namedtuple('BIDSLayout', ['root'])
        wf = init_dwi_concat_wf(layout=BIDSLayout('.'))

    **Parameters**

        layout : BIDSLayout object
            BIDS dataset layout

    **Inputs**

        ref_file
            reference dwi NIfTI file
        dwi_list : :obj:`list`
            list of dwi NIfTI files

    **Outputs**

        dwi_file : :obj:`str`
            concatenated dwi NIfTI file
        bvec_file
            concatenated bvec file
        bval_file
            concatenated bval file

    """

    wf = pe.Workflow(name='dwi_concat_wf')

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['ref_file', 'dwi_list']),
        name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['dwi_file', 'bvec_file', 'bval_file']),
        name='outputnode')

    def gather_bvec_bval(layout, dwi_list):
        bvec_list = [layout.get_bvec(bvec) for bvec in dwi_list]
        bval_list = [layout.get_bval(bval) for bval in dwi_list]
        return bvec_list, bval_list

    gather_bvec_bval = pe.Node(
        niu.Function(
            input_names=['layout', 'dwi_list'],
            output_names=['bvec_list', 'bval_list'],
            function=gather_bvec_bval
        ),
        name='gather_bvec_bval')
    gather_bvec_bval.inputs.layout = layout

    def concat_dwis(ref_file, dwi_list):
        import os
        import numpy as np
        from nipype.utils.filemanip import fname_presuffix
        import nibabel as nib
        from nilearn.image import concat_imgs

        out_file = fname_presuffix(
            ref_file,
            newpath=os.path.abspath('.')
        )

        dwi_data = [nib.load(dwi) for dwi in dwi_list]

        new_nii = concat_imgs(dwi_data)

        hdr = dwi_data[0].header.copy()
        hdr.set_data_shape(new_nii.shape)
        hdr.set_xyzt_units('mm')
        hdr.set_data_dtype(np.float32)
        nib.Nifti1Image(new_nii.get_data(), dwi_data[0].affine, hdr).to_filename(out_file)
        return out_file

    concat_dwis = pe.Node(
        niu.Function(
            input_names=['ref_file', 'dwi_list'],
            output_names=['out_file'],
            function=concat_dwis
        ),
        name='concat_dwis')

    def concat_bvecs(ref_file, bvec_list):
        import os
        import numpy as np
        from nipype.utils.filemanip import fname_presuffix

        out_file = fname_presuffix(
            ref_file,
            suffix='.bvec',
            newpath=os.path.abspath('.'),
            use_ext=False
        )

        bvec_vals = []
        for bvec in bvec_list:
            bvec_vals.append(np.genfromtxt(bvec))
        np.savetxt(out_file,
                   np.concatenate((bvec_vals), axis=1),
                   fmt='%.4f',
                   delimiter=' ')
        return out_file

    concat_bvecs = pe.Node(
        niu.Function(
            input_names=['ref_file', 'bvec_list'],
            output_names=['out_file'],
            function=concat_bvecs
        ),
        name='concat_bvecs')

    def concat_bvals(ref_file, bval_list):
        import os
        import numpy as np
        from nipype.utils.filemanip import fname_presuffix

        out_file = fname_presuffix(
            ref_file,
            suffix='.bval',
            newpath=os.path.abspath('.'),
            use_ext=False
        )

        bval_vals = []
        for bval in bval_list:
            bval_vals.append(np.genfromtxt(bval))
        np.savetxt(out_file,
                   np.concatenate((bval_vals), axis=0),
                   fmt='%i',
                   delimiter=' ',
                   newline=' ')
        return out_file

    concat_bvals = pe.Node(
        niu.Function(
            input_names=['ref_file', 'bval_list'],
            output_names=['out_file'],
            function=concat_bvals
        ),
        name='concat_bvals')

    wf.connect([
        (inputnode, gather_bvec_bval, [('dwi_list', 'dwi_list')]),
        (inputnode, concat_dwis, [('ref_file', 'ref_file'),
                                  ('dwi_list', 'dwi_list')]),
        (inputnode, concat_bvecs, [('ref_file', 'ref_file')]),
        (gather_bvec_bval, concat_bvecs, [('bvec_list', 'bvec_list')]),
        (inputnode, concat_bvals, [('ref_file', 'ref_file')]),
        (gather_bvec_bval, concat_bvals, [('bval_list', 'bval_list')]),
        (concat_dwis, outputnode, [('merged_file', 'dwi_file')]),
        (concat_bvecs, outputnode, [('out_file', 'bvec_file')]),
        (concat_bvals, outputnode, [('out_file', 'bval_file')])
    ])

    return wf
