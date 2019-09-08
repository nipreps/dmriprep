# -*- coding: utf-8 -*-

"""
Utility workflows
^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_concat_wf

"""
import os
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu


def init_dwi_concat_wf(dwi_files, fbvals, fbvecs, metadata_files, sub, ses, out_dir):
    """
    This workflow concatenates a list of dwi images as well as their associated
    bvecs and bvals.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.dwi import init_dwi_concat_wf
        wf = init_dwi_concat_wf(ref_file='/madeup/path/sub-01_dwi.nii.gz')

    **Inputs**

        dwis : :obj:`list`
            list of dwi NIfTI files
        fbvecs : :obj:`list`
            list of associated bvec files
        fbvals : :obj:`list`
            list of associated bval files

    **Outputs**

        dwi_file : :obj:`str`
            concatenated dwi NIfTI file
        bvec_file
            concatenated bvec file
        bval_file
            concatenated bval file

    """
    import_list = [
        "import sys",
        "import os",
        "import numpy as np",
        "import nibabel as nib",
        "import warnings",
        'warnings.filterwarnings("ignore")',
    ]

    subdir = "%s%s%s" % (out_dir, "/", sub)
    if not os.path.isdir(subdir):
        os.mkdir(subdir)
    sesdir = "%s%s%s%s%s" % (out_dir, "/", sub, "/ses-", ses)
    if not os.path.isdir(sesdir):
        os.mkdir(sesdir)

    wf = pe.Workflow(name='dwi_concat_wf')
    wf.base_dir = '/tmp'

    inputnode = pe.Node(niu.IdentityInterface(fields=['dwi_list',
                                                      'bvec_list',
                                                      'bval_list',
                                                      'metadata_list',
                                                      'sesdir']),
                        name='inputnode')

    inputnode.inputs.bval_list = fbvals
    inputnode.inputs.bvec_list = fbvecs
    inputnode.inputs.dwi_list = dwi_files
    inputnode.inputs.metadata_list = metadata_files
    inputnode.inputs.sesdir = sesdir

    outputnode = pe.Node(niu.IdentityInterface(fields=['dwi_file',
                                                       'bvec_file',
                                                       'bval_file',
                                                       'metadata_file']),
                         name='outputnode')

    def concat_dwis(sesdir, dwi_list):
        import nibabel as nib
        import numpy as np
        import os
        from nilearn.image import concat_imgs

        out_file = sesdir + '/' + os.path.basename(dwi_list[0]).split('_acq')[0] + '_concat.nii.gz'

        dwi_data = [nib.load(dwi_file) for dwi_file in dwi_list]

        new_nii = concat_imgs(dwi_data)

        hdr = dwi_data[0].header.copy()
        hdr.set_data_shape(new_nii.shape)
        hdr.set_xyzt_units('mm')
        hdr.set_data_dtype(np.float32)
        nib.Nifti1Image(new_nii.get_data(), dwi_data[0].affine, hdr).to_filename(out_file)
        return out_file

    concat_dwis = pe.Node(
        niu.Function(
            input_names=['sesdir', 'dwi_list'],
            output_names=['out_file'],
            function=concat_dwis
        ),
        imports=import_list,
        name='concat_dwis')

    def concat_bvecs(sesdir, bvec_list):
        import numpy as np
        import os
        out_file = sesdir + '/' + os.path.basename(bvec_list[0]).split('_acq')[0] + '_concat.bvec'

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
            input_names=['sesdir', 'bvec_list'],
            output_names=['out_file'],
            function=concat_bvecs
        ),
        imports=import_list,
        name='concat_bvecs')

    def concat_bvals(sesdir, bval_list):
        import numpy as np
        import os
        out_file = sesdir + '/' + os.path.basename(bval_list[0]).split('_acq')[0] + '_concat.bval'

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
            input_names=['sesdir', 'bval_list'],
            output_names=['out_file'],
            function=concat_bvals
        ),
        imports=import_list,
        name='concat_bvals')

    def summarize_metadata(sesdir, metadata_list, bval_list):
        import numpy as np
        import json
        import os
        out_file = sesdir + '/' + os.path.basename(metadata_list[0]).split('_acq')[0] + '_metadata_concat_summary.json'

        bval_vals = []
        for bval in bval_list:
            bval_vals.append(np.genfromtxt(bval).astype('bool').astype('int').tolist())

        bval_config = [sum(bval) for bval in bval_vals]

        metadata_dicts = []
        i = 1
        for json_file in metadata_list:
            with open(json_file, "r") as f:
                metadata_dict = json.load(f)
            for param in list(metadata_dict.keys()):
                metadata_dict[param + '_' + str(i)] = metadata_dict.pop(param)
            metadata_dicts.append(metadata_dict)
            i = i + 1

        metadata_megadict = dict(metadata_dicts[0])
        for dic in metadata_dicts:
            metadata_megadict.update(dic)

        metadata_megadict['vol_legend'] = bval_config

        with open(out_file, 'w') as json_file:
            json.dump(metadata_megadict, json_file)

        return out_file

    summarize_metadata = pe.Node(
        niu.Function(
            input_names=['sesdir', 'metadata_list', 'bval_list'],
            output_names=['out_file'],
            function=summarize_metadata
        ),
        imports=import_list,
        name='summarize_metadata')

    wf.connect([
        (inputnode, concat_dwis, [('sesdir', 'sesdir'),
                                  ('dwi_list', 'dwi_list')]),
        (inputnode, concat_bvecs, [('sesdir', 'sesdir'),
                                   ('bvec_list', 'bvec_list')]),
        (inputnode, concat_bvals, [('sesdir', 'sesdir'),
                                   ('bval_list', 'bval_list')]),
        (inputnode, summarize_metadata, [('sesdir', 'sesdir'),
                                         ('metadata_list', 'metadata_list'),
                                         ('bval_list', 'bval_list')]),
        (concat_dwis, outputnode, [('out_file', 'dwi_file')]),
        (concat_bvecs, outputnode, [('out_file', 'bvec_file')]),
        (concat_bvals, outputnode, [('out_file', 'bval_file')]),
        (summarize_metadata, outputnode, [('out_file', 'metadata_file')])
    ])

    return wf
