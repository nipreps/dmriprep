# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Utility workflows
^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_reference_wf
.. autofunction:: init_enhance_and_skullstrip_dwi_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu, fsl, afni

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from niworkflows.interfaces.images import ValidateImage
from niworkflows.interfaces.fixes import FixN4BiasFieldCorrection as N4BiasFieldCorrection
from niworkflows.interfaces.masks import SimpleShowMaskRPT
from niworkflows.interfaces.utils import CopyXForm

from ...interfaces.images import MeanB0

DEFAULT_MEMORY_MIN_GB = 0.01


def init_dwi_reference_wf(omp_nthreads, dwi_file=None,
                          name='dwi_reference_wf', gen_report=False):
    """
    Build a workflow that generates a reference b0 image from a dwi series.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.dwi.util import init_dwi_reference_wf
        wf = init_dwi_reference_wf(omp_nthreads=1)

    **Parameters**

        dwi_file : str
            dwi NIfTI file
        omp_nthreads : int
            Maximum number of threads an individual process may use
        name : str
            Name of workflow (default: ``dwi_reference_wf``)
        gen_report : bool
            Whether a mask report node should be appended in the end

    **Inputs**

        dwi_file
            dwi NIfTI file

    **Outputs**

        dwi_file
            Validated dwi NIfTI file
        raw_ref_image
            Reference image to which dwi series is motion corrected
        ref_image
            Contrast-enhanced reference image
        ref_image_brain
            Skull-stripped reference image
        dwi_mask
            Skull-stripping mask of reference image
        validation_report
            HTML reportlet indicating whether ``dwi_file`` had a valid affine


    **Subworkflows**

        * :py:func:`~dmriprep.workflows.dwi.util.init_enhance_and_skullstrip_wf`

    """
    workflow = Workflow(name=name)
    workflow.__desc__ = """\
First, a reference volume and its skull-stripped version were generated
using a custom methodology taken from *fMRIPrep*.
"""
    inputnode = pe.Node(niu.IdentityInterface(fields=['dwi_file', 'bvec_file', 'bval_file']),
                        name='inputnode')
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['dwi_file', 'raw_ref_image',
                                      'ref_image', 'ref_image_brain',
                                      'dwi_mask', 'validation_report']),
        name='outputnode')

    # Simplify manually setting input image
    if dwi_file is not None:
        inputnode.inputs.dwi_file = dwi_file

    validate = pe.Node(ValidateImage(), name='validate', mem_gb=DEFAULT_MEMORY_MIN_GB)

    gen_ref = pe.Node(MeanB0(), name="gen_ref")

    pre_mask = pe.Node(afni.Automask(outputtype="NIFTI_GZ"), name="pre_mask")

    enhance_and_skullstrip_dwi_wf = init_enhance_and_skullstrip_dwi_wf(
        omp_nthreads=omp_nthreads)

    workflow.connect([
        (inputnode, validate, [('dwi_file', 'in_file')]),
        (validate, gen_ref, [('out_file', 'in_file')]),
        (inputnode, gen_ref, [('bvec_file', 'in_bvec'),
                              ('bval_file', 'in_bval')]),
        (gen_ref, pre_mask, [('out_file', 'in_file')]),
        (gen_ref, enhance_and_skullstrip_dwi_wf, [('out_file', 'inputnode.in_file')]),
        (pre_mask, enhance_and_skullstrip_dwi_wf, [('out_file', 'inputnode.pre_mask')]),
        (validate, outputnode, [('out_file', 'dwi_file'),
                                ('out_report', 'validation_report')]),
        (gen_ref, outputnode, [('out_file', 'raw_ref_image')]),
        (enhance_and_skullstrip_dwi_wf, outputnode, [
            ('outputnode.bias_corrected_file', 'ref_image'),
            ('outputnode.mask_file', 'dwi_mask'),
            ('outputnode.skull_stripped_file', 'ref_image_brain')]),
    ])

    if gen_report:
        mask_reportlet = pe.Node(SimpleShowMaskRPT(), name='mask_reportlet')
        workflow.connect([
            (enhance_and_skullstrip_dwi_wf, mask_reportlet, [
                ('outputnode.bias_corrected_file', 'background_file'),
                ('outputnode.mask_file', 'mask_file'),
            ]),
        ])

    return workflow


def init_enhance_and_skullstrip_dwi_wf(
        name='enhance_and_skullstrip_dwi_wf',
        omp_nthreads=1):
    """
    This workflow takes in a dwi reference iamge and sharpens the histogram
    with the application of the N4 algorithm for removing the
    :abbr:`INU (intensity non-uniformity)` bias field and calculates a signal
    mask.

    Steps of this workflow are:

      1. Run ANTs' ``N4BiasFieldCorrection`` on the input
         dwi reference image and mask.
      2. Calculate a loose mask using FSL's ``bet``, with one mathematical morphology
         dilation of one iteration and a sphere of 6mm as structuring element.
      3. Mask the :abbr:`INU (intensity non-uniformity)`-corrected image
         with the latest mask calculated in 3), then use AFNI's ``3dUnifize``
         to *standardize* the T2* contrast distribution.
      4. Calculate a mask using AFNI's ``3dAutomask`` after the contrast
         enhancement of 4).
      5. Calculate a final mask as the intersection of 2) and 4).
      6. Apply final mask on the enhanced reference.

    .. workflow ::
        :graph2use: orig
        :simple_form: yes

        from dmriprep.workflows.dwi.util import init_enhance_and_skullstrip_dwi_wf
        wf = init_enhance_and_skullstrip_dwi_wf(omp_nthreads=1)

    **Parameters**
        name : str
            Name of workflow (default: ``enhance_and_skullstrip_dwi_wf``)
        omp_nthreads : int
            number of threads available to parallel nodes

    **Inputs**

        in_file
            b0 image (single volume)
        pre_mask
            initial mask

    **Outputs**

        bias_corrected_file
            the ``in_file`` after `N4BiasFieldCorrection`_
        skull_stripped_file
            the ``bias_corrected_file`` after skull-stripping
        mask_file
            mask of the skull-stripped input file
        out_report
            reportlet for the skull-stripping

    .. _N4BiasFieldCorrection: https://hdl.handle.net/10380/3053
    """
    workflow = Workflow(name=name)
    inputnode = pe.Node(niu.IdentityInterface(fields=['in_file', 'pre_mask']),
                        name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=[
        'mask_file', 'skull_stripped_file', 'bias_corrected_file']), name='outputnode')

    # Run N4 normally, force num_threads=1 for stability (images are small, no need for >1)
    n4_correct = pe.Node(N4BiasFieldCorrection(
        dimension=3, copy_header=True, bspline_fitting_distance=200), shrink_factor=2,
        name='n4_correct', n_procs=1)
    n4_correct.inputs.rescale_intensities = True

    # Create a generous BET mask out of the bias-corrected EPI
    skullstrip_first_pass = pe.Node(fsl.BET(frac=0.2, mask=True),
                                    name='skullstrip_first_pass')
    bet_dilate = pe.Node(fsl.DilateImage(
        operation='max', kernel_shape='sphere', kernel_size=6.0,
        internal_datatype='char'), name='skullstrip_first_dilate')
    bet_mask = pe.Node(fsl.ApplyMask(), name='skullstrip_first_mask')

    # Use AFNI's unifize for T2 constrast & fix header
    unifize = pe.Node(afni.Unifize(
        t2=True, outputtype='NIFTI_GZ',
        # Default -clfrac is 0.1, 0.4 was too conservative
        # -rbt because I'm a Jedi AFNI Master (see 3dUnifize's documentation)
        args='-clfrac 0.2 -rbt 18.3 65.0 90.0',
        out_file="uni.nii.gz"), name='unifize')
    fixhdr_unifize = pe.Node(CopyXForm(), name='fixhdr_unifize', mem_gb=0.1)

    # Run ANFI's 3dAutomask to extract a refined brain mask
    skullstrip_second_pass = pe.Node(afni.Automask(dilate=1,
                                                   outputtype='NIFTI_GZ'),
                                     name='skullstrip_second_pass')
    fixhdr_skullstrip2 = pe.Node(CopyXForm(), name='fixhdr_skullstrip2', mem_gb=0.1)

    # Take intersection of both masks
    combine_masks = pe.Node(fsl.BinaryMaths(operation='mul'),
                            name='combine_masks')

    # Compute masked brain
    apply_mask = pe.Node(fsl.ApplyMask(), name='apply_mask')

    workflow.connect([
        (inputnode, n4_correct, [('in_file', 'input_image'),
                                 ('pre_mask', 'mask_image')]),
        (inputnode, fixhdr_unifize, [('in_file', 'hdr_file')]),
        (inputnode, fixhdr_skullstrip2, [('in_file', 'hdr_file')]),
        (n4_correct, skullstrip_first_pass, [('output_image', 'in_file')]),
        (skullstrip_first_pass, bet_dilate, [('mask_file', 'in_file')]),
        (bet_dilate, bet_mask, [('out_file', 'mask_file')]),
        (skullstrip_first_pass, bet_mask, [('out_file', 'in_file')]),
        (bet_mask, unifize, [('out_file', 'in_file')]),
        (unifize, fixhdr_unifize, [('out_file', 'in_file')]),
        (fixhdr_unifize, skullstrip_second_pass, [('out_file', 'in_file')]),
        (skullstrip_first_pass, combine_masks, [('mask_file', 'in_file')]),
        (skullstrip_second_pass, fixhdr_skullstrip2, [('out_file', 'in_file')]),
        (fixhdr_skullstrip2, combine_masks, [('out_file', 'operand_file')]),
        (fixhdr_unifize, apply_mask, [('out_file', 'in_file')]),
        (combine_masks, apply_mask, [('out_file', 'mask_file')]),
        (combine_masks, outputnode, [('out_file', 'mask_file')]),
        (apply_mask, outputnode, [('out_file', 'skull_stripped_file')]),
        (n4_correct, outputnode, [('output_image', 'bias_corrected_file')]),
    ])

    return workflow
