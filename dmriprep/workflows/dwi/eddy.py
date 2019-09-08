# -*- coding: utf-8 -*-

"""
Head motion, eddy current distortion and EPI distortion correction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_eddy_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, utility as niu
from numba import cuda


def init_dwi_eddy_wf(omp_nthreads, sdc_method):
    """
    This workflow runs eddy on the input dwi image.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.dwi import init_dwi_eddy_wf
        wf = init_dwi_eddy_wf(omp_nthreads=1, sdc_method='nonlinear_reg')

    **Parameters**

        omp_nthreads: int
            Number of threads to run eddy
        sdc_type: str
            Synthetic distortion correction method (may include 'fieldmap, 'topup', 'nonlinear_reg')

    **Inputs**

        dwi_file
            dwi NIfTI file
        bvec_file
            bvec file
        bval_file
            bval file
        mask_file
            brain mask file
        fieldmap_file
            fieldmap file
        topup_fieldcoef
            topup file containing field coefficients
        topup_movpar
            topup movpar.txt file
        acqp
            acquisition parameters file
        index
            index file

    **Outputs**

        out_file
            output eddy-corrected dwi image
        out_bvec
            output rotated bvecs after eddy correction

    """

    wf = pe.Workflow(name='dwi_eddy_wf')

    inputnode = pe.Node(niu.IdentityInterface(fields=['dwi_file',
                                                      'bvec_file',
                                                      'bval_file',
                                                      'mask_file',
                                                      'fieldmap_file',
                                                      'topup_fieldcoef',
                                                      'topup_movpar',
                                                      'acqp',
                                                      'index']),
                       name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file', 'out_bvec']),
                         name='outputnode')

    ecc = pe.Node(
        fsl.Eddy(num_threads=omp_nthreads, repol=True, cnr_maps=True, residuals=True),
        name='fsl_eddy')

    try:
        if cuda.gpus:
            ecc.inputs.use_cuda = True
    except:
        ecc.inputs.use_cuda = False

    wf.connect([
        (inputnode, ecc, [('dwi_file', 'in_file'),
                          ('bval_file', 'in_bval'),
                          ('bvec_file', 'in_bvec'),
                          ('acqp', 'in_acqp'),
                          ('index', 'in_index'),
                          ('mask_file', 'in_mask')]),
        (ecc, outputnode, [('out_corrected', 'out_file'),
                           ('out_rotated_bvecs', 'out_bvec')])
    ])

    if sdc_method == 'fieldmap':
        wf.connect([
            (inputnode, ecc, [('fieldmap_file', 'field')])
        ])

    if sdc_method == 'topup':
        wf.connect([
            (inputnode, ecc, [('topup_fieldcoef', 'in_topup_fieldcoef'),
                              ('topup_movpar', 'in_topup_movpar')])
        ])

    return wf
