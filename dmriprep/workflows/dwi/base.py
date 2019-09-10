# -*- coding: utf-8 -*-

"""
Orchestrating the dwi preprocessing workflows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_preproc_wf

"""

from nipype import logging
from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, mrtrix3, utility as niu

from niworkflows.engine.workflows import LiterateWorkflow as Workflow

from .artifacts import init_dwi_artifacts_wf
from .eddy import init_dwi_eddy_wf
from .tensor import init_dwi_tensor_wf
from ..fieldmap.base import init_sdc_wf

FMAP_PRIORITY = {'epi': 0, 'fieldmap': 1, 'phasediff': 2, 'phase': 3, 'syn': 4}

DEFAULT_MEMORY_MIN_GB = 0.01
LOGGER = logging.getLogger('nipype.workflow')


def init_dwi_preproc_wf(
    acqp_file,
    b0_thresh,
    debug,
    dwi_file,
    eddy_config,
    fmap_bspline,
    force_syn,
    freesurfer,
    ignore,
    layout,
    low_mem,
    num_dwi,
    omp_nthreads,
    output_dir,
    output_resolution,
    output_spaces,
    reportlets_dir,
    use_syn,
):
    """
    This workflow controls the diffusion preprocessing stages of dMRIPrep.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from collections import namedtuple
        from dmriprep.workflows.dwi import init_dwi_preproc_wf
        BIDSLayout = namedtuple('BIDSLayout', ['root'])
        wf = init_dwi_preproc_wf(
            acqp_file='',
            b0_thresh=5,
            debug=False,
            dwi_file='/madeup/path/sub-01_dwi.nii.gz',
            eddy_config='',
            fmap_bspline=False,
            force_syn=False,
            freesurfer=True,
            ignore=[],
            layout=BIDSLayout('.'),
            low_mem=False,
            num_dwi=1,
            omp_nthreads=1,
            output_dir='.',
            output_resolution=(1, 1, 1),
            output_spaces=OrderedDict([('dwi', {})]),
            reportlets_dir='.',
            use_syn=True
        )

    **Subworkflows**

        * :py:func:`~dmriprep.workflows.dwi.util.init_dwi_concat_wf`
        * :py:func:`~dmriprep.workflows.dwi.artifacts.init_dwi_artifacts_wf`
        * :py:func:`~dmriprep.workflows.dwi.eddy.init_dwi_eddy_wf`
        * :py:func:`~dmriprep.workflows.dwi.tensor.init_dwi_tensor_wf`

    """

    wf_name = _get_wf_name(dwi_file)

    if isinstance(dwi_file, list):
        ref_file = dwi_file[0]
    else:
        ref_file = dwi_file

    # sdc_method = None

    # For doc building purposes
    if not hasattr(layout, 'parse_file_entities'):
        metadata = {
            'PhaseEncodingDirection': 'j-',
            'TotalReadoutTime': 0.05
        }
        fmaps = [{
            'suffix': 'phasediff',
            'phasediff': 'sub-01/fmap/sub-01_phasediff.nii.gz',
            'magnitude1': 'sub-01/fmap/sub-01_magnitude1.nii.gz',
            'magnitude2': 'sub-01/fmap/sub-01_magnitude2.nii.gz'
        }]
    else:
        metadata = layout.get_metadata(ref_file)
        # Find fieldmaps. Options: (epi|fieldmap|phasediff|phase1|phase2|syn)
        fmaps = []
        if 'fieldmaps' not in ignore:
            for fmap in layout.get_fieldmap(ref_file, return_list=True):
                fmap['metadata'] = layout.get_metadata(fmap[fmap['suffix']])
                fmaps.append(fmap)

        if force_syn or (use_syn and not fmaps):
            fmaps.append({'suffix': 'syn'})

        # if fmaps:
        #     fmaps.sort(key=lambda fmap: FMAP_PRIORITY[fmap['suffix']])
        #     fmap = fmaps[0]
        #     if fmap['suffix'] == 'epi':
        #         sdc_method = 'topup'
        #     if any(s in fmap['suffix'] for s in ['fieldmap', 'phasediff', 'phase1']):
        #         sdc_method = 'fieldmap'

    dwi_wf = Workflow(name=wf_name)
    dwi_wf.__desc__ = """

Diffusion data preprocessing

: For each of the {num_dwi} diffusion runs found per subject (across all
sessions), the following preprocessing was performed.
""".format(num_dwi=num_dwi)

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['dwi_file', 'bvec_file', 'bval_file',
                'subjects_dir', 'subject_id',
                't1_brain', 'template', 'std2anat_xfm']),
        name='inputnode')
    inputnode.inputs.dwi_file = dwi_file
    inputnode.inputs.bvec_file = layout.get_bvec(dwi_file)
    inputnode.inputs.bval_file = layout.get_bval(dwi_file)

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                'out_dwi',
                'out_bval',
                'out_bvec',
                'index',
                'acq_params',
                'out_mask',
                'out_b0_pre',
                'out_b0_mask_pre',
                'out_eddy_quad_json',
                'out_eddy_quad_pdf',
                'out_dtifit_FA',
                'out_dtifit_V1',
                'out_dtifit_sse',
                'out_noise']),
        name='outputnode')

    def gen_index(in_file):
        """
        Create an index file that tells `eddy` which line/lines in the
        `acqparams.txt` file are relevant for the dwi data passed into `eddy`

        **Inputs**

        in_file
            The bval file.

        **Outputs**

        out_file
            The output index file.

        """

        import os
        import numpy as np
        import nibabel as nib
        from nipype.utils import NUMPY_MMAP
        from nipype.utils.filemanip import fname_presuffix

        out_file = fname_presuffix(
            in_file, suffix='_index.txt', newpath=os.path.abspath('.'), use_ext=False
        )
        vols = nib.load(in_file, mmap=NUMPY_MMAP).get_data().shape[-1]
        index_lines = np.ones((vols,))
        index_lines_reshape = index_lines.reshape(1, index_lines.shape[0])
        np.savetxt(out_file, index_lines_reshape, fmt='%i')
        return out_file

    gen_idx = pe.Node(
        niu.Function(
            input_names=['in_file'], output_names=['out_file'], function=gen_index),
        name='gen_index')

    def gen_acqparams(in_file, metadata):
        """
        Create an acquisition parameters file for ``eddy``

        **Inputs**

        in_file
            The dwi file
        metadata
            The BIDS metadata of the dwi file

        **Outputs**

        out_file
            The output acquisition parameters file

        """

        import os
        from nipype.utils.filemanip import fname_presuffix

        out_file = fname_presuffix(
            in_file,
            suffix='_acqparams.txt',
            newpath=os.path.abspath('.'),
            use_ext=False,
        )

        acq_param_dict = {
            'j': '0 1 0 %.7f',
            'j-': '0 -1 0 %.7f',
            'i': '1 0 0 %.7f',
            'i-': '-1 0 0 %.7f',
            'k': '0 0 1 %.7f',
            'k-': '0 0 -1 %.7f',
        }

        pe_dir = metadata.get('PhaseEncodingDirection')
        total_readout = metadata.get('TotalReadoutTime')
        acq_param_lines = acq_param_dict[pe_dir] % total_readout

        with open(out_file, 'w') as f:
            f.write(acq_param_lines)

        return out_file

    acqp = pe.Node(
        niu.Function(
            input_names=['in_file', 'metadata'],
            output_names=['out_file'],
            function=gen_acqparams),
        name='acqp')

    dwi_artifacts_wf = init_dwi_artifacts_wf(ignore, output_resolution)

    def b0_average(in_dwi, in_bval, b0_thresh, out_file=None):
        """
        Averages the *b0* volumes from a DWI dataset.
        As current dMRI data are being acquired with all b-values > 0.0,
        the *lowb* volumes are selected by specifying the parameter b0_thresh.
        .. warning:: *b0* should be already registered (head motion artifact
        should be corrected).
        """
        import os
        import numpy as np
        import nibabel as nib
        from nipype.utils import NUMPY_MMAP
        from nipype.utils.filemanip import fname_presuffix

        if out_file is None:
            out_file = fname_presuffix(
                in_dwi, suffix='_avg_b0', newpath=os.path.abspath('.')
            )

        imgs = np.array(nib.four_to_three(nib.load(in_dwi, mmap=NUMPY_MMAP)))
        bval = np.loadtxt(in_bval)
        index = np.argwhere(bval <= b0_thresh).flatten().tolist()

        b0s = [im.get_data().astype(np.float32) for im in imgs[index]]
        b0 = np.average(np.array(b0s), axis=0)

        hdr = imgs[0].header.copy()
        hdr.set_data_shape(b0.shape)
        hdr.set_xyzt_units('mm')
        hdr.set_data_dtype(np.float32)
        nib.Nifti1Image(b0, imgs[0].affine, hdr).to_filename(out_file)
        return out_file

    avg_b0_0 = pe.Node(
        niu.Function(
            input_names=['in_dwi', 'in_bval', 'b0_thresh'],
            output_names=['out_file'],
            function=b0_average),
        name='b0_avg_pre')

    avg_b0_0.inputs.b0_thresh = b0_thresh

    bet_dwi0 = pe.Node(
        fsl.BET(frac=0.3, mask=True, robust=True), name='bet_dwi_pre'
    )

    dwi_sdc_wf = init_sdc_wf(
        fmaps,
        layout,
        metadata
    )

    dwi_eddy_wf = init_dwi_eddy_wf(omp_nthreads, sdc_method)

    denoise_eddy = pe.Node(mrtrix3.DWIDenoise(), name='denoise_eddy')

    eddy_quad = pe.Node(fsl.EddyQuad(verbose=True), name='eddy_quad')

    get_path = lambda x: x.split('.nii.gz')[0].split('_fix')[0]
    get_qc_path = lambda x: x.split('.nii.gz')[0] + '.qc'

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name='fslroi')

    bias_correct = pe.Node(mrtrix3.DWIBiasCorrect(use_ants=True), name='bias_correct')

    def get_b0_mask_fn(b0_file):
        import os
        import nibabel as nib
        from nipype.utils.filemanip import fname_presuffix
        from dipy.segment.mask import median_otsu

        mask_file = fname_presuffix(
            b0_file, suffix='_mask', newpath=os.path.abspath('.')
        )
        img = nib.load(b0_file)
        data, aff = img.get_data(), img.affine
        _, mask = median_otsu(data, 2, 1)
        nib.Nifti1Image(mask.astype(float), aff).to_filename(mask_file)
        return mask_file

    b0mask_node = pe.Node(
        niu.Function(
            input_names=['b0_file'], output_names=['mask_file'], function=get_b0_mask_fn),
        name='getB0Mask')

    dwi_tensor_wf = init_dwi_tensor_wf()

    dwi_wf.connect([
        (inputnode, gen_idx, [('dwi_file', 'in_file')]),
        (inputnode, acqp, [('dwi_file', 'in_file'), ('dwi_meta', 'metadata')]),
        (inputnode, dwi_artifacts_wf, [('dwi_file', 'inputnode.dwi_file')]),
        (dwi_artifacts_wf, avg_b0_0, [('outputnode.out_file', 'in_dwi')]),
        (dwi_artifacts_wf, dwi_eddy_wf, [('outputnode.out_file', 'inputnode.dwi_file')]),
        (inputnode, avg_b0_0, [('bval_file', 'in_bval')]),
        (avg_b0_0, bet_dwi0, [('out_file', 'in_file')]),
        (inputnode, dwi_eddy_wf, [('bval_file', 'inputnode.bval_file'),
                                  ('bvec_file', 'inputnode.bvec_file')]),
        (bet_dwi0, dwi_eddy_wf, [('mask_file', 'inputnode.mask_file')]),
        (gen_idx, dwi_eddy_wf, [('out_file', 'inputnode.index')]),
        (dwi_eddy_wf, denoise_eddy, [('outputnode.out_file', 'in_file')]),
        (dwi_eddy_wf, bias_correct, [('outputnode.out_file', 'in_file'),
                                     ('outputnode.out_bvec', 'in_bvec')]),
        (inputnode, bias_correct, [('bval_file', 'in_bval')]),
        (bias_correct, fslroi, [('out_file', 'in_file')]),
        (fslroi, b0mask_node, [('roi_file', 'b0_file')]),
        (dwi_eddy_wf, eddy_quad, [(('outputnode.out_file', get_path), 'base_name'),
                                  (('outputnode.out_file', get_qc_path), 'output_dir'),
                                  ('outputnode.out_bvec', 'bvec_file')]),
        (inputnode, eddy_quad, [('bval_file', 'bval_file')]),
        (b0mask_node, eddy_quad, [('mask_file', 'mask_file')]),
        (gen_idx, eddy_quad, [('out_file', 'idx_file')]),
        (bias_correct, dwi_tensor_wf, [('out_file', 'inputnode.dwi_file')]),
        (b0mask_node, dwi_tensor_wf, [('mask_file', 'inputnode.mask_file')]),
        (inputnode, dwi_tensor_wf, [('bval_file', 'inputnode.bval_file')]),
        (dwi_eddy_wf, dwi_tensor_wf, [('outputnode.out_bvec', 'inputnode.bvec_file')])
    ])

    if acqp_file:
        eddy_inputspec = dwi_eddy_wf.get_node('inputnode')
        eddy_inputspec.inputs.acqp = acqp_file
        eddy_quad.inputs.param_file = acqp_file
    else:
        dwi_wf.connect([
            (acqp, dwi_eddy_wf, [('out_file', 'inputnode.acqp')]),
            (acqp, eddy_quad, [('out_file', 'param_file')])
        ])

    # Decide what ecc will take: topup or fmap
    # If epi files detected
    if fmaps:
        if fmap['suffix'] == 'epi':
            dwi_wf.connect([
                (dwi_sdc_wf, dwi_eddy_wf, [('outputnode.out_topup', 'inputnode.topup_fieldcoef'),
                                           ('outputnode.out_movpar', 'inputnode.topup_movpar')])
            ])
    # Otherwise (fieldmaps)
        if any(s in fmap['suffix'] for s in ['fieldmap', 'phasediff', 'phase1']):
            dwi_wf.connect([
                (bet_dwi0, dwi_sdc_wf, [('out_file', 'inputnode.b0_stripped')]),
                (dwi_sdc_wf, dwi_eddy_wf, [('outputnode.out_fmap', 'inputnode.fieldmap_file')])
            ])

    dwi_wf.connect([
        (dwi_eddy_wf, outputnode, [('outputnode.out_file', 'out_dwi')]),
        (inputnode, outputnode, [('bval_file', 'out_bval')]),
        (dwi_eddy_wf, outputnode, [('outputnode.out_bvec', 'out_bvec')]),
        (gen_idx, outputnode, [('out_file', 'index')]),
        (acqp, outputnode, [('out_file', 'acq_params')]),
        (b0mask_node, outputnode, [('mask_file', 'out_mask')]),
        (avg_b0_0, outputnode, [('out_file', 'out_b0_pre')]),
        (bet_dwi0, outputnode, [('mask_file', 'out_b0_mask_pre')]),
        (eddy_quad, outputnode, [('qc_json', 'out_eddy_quad_json'),
                                 ('qc_pdf', 'out_eddy_quad_pdf')]),
        (dwi_tensor_wf, outputnode, [('outputnode.FA_file', 'out_dtifit_FA'),
                                     ('outputnode.MD_file', 'out_dtifit_MD'),
                                     ('outputnode.AD_file', 'out_dtifit_AD'),
                                     ('outputnode.RD_file', 'out_dtifit_RD'),
                                     ('outputnode.V1_file', 'out_dtifit_V1'),
                                     ('outputnode.sse_file', 'out_dtifit_sse')])
    ])

    return dwi_wf


def _get_wf_name(dwi_fname):
    """
    Derives the workflow name from the supplied dwi file.
    """

    from nipype.utils.filemanip import split_filename

    fname = split_filename(dwi_fname)[1]
    fname_nosub = '_'.join(fname.split('_')[1:])
    name = 'dwi_preproc_' + fname_nosub.replace('.', '_').replace(' ', '').replace(
        '-', '_'
    ).replace('_dwi', '_wf')

    return name
