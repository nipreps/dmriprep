"""Utility workflows for :abbr:`DWI (diffusion weighted imaging)` data."""

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu, fsl, afni

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from niworkflows.interfaces.images import ValidateImage
from niworkflows.interfaces.fixes import (
    FixN4BiasFieldCorrection as N4BiasFieldCorrection,
)
from niworkflows.interfaces.nibabel import ApplyMask
from niworkflows.interfaces.utils import CopyXForm

from ...interfaces.images import ExtractB0, RescaleB0


def init_dwi_reference_wf(mem_gb, omp_nthreads, name="dwi_reference_wf"):
    """
    Build a workflow that generates a reference :math:`b = 0` image from a DWI dataset.

    To generate the reference *b0*, this workflow takes in a DWI dataset,
    extracts the b0s, registers them to each other, rescales the signal
    intensity values, and calculates a median image.

    Then, the reference *b0* and its skull-stripped version are generated using
    a custom methodology adapted from *niworkflows*.

    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes

            from dmriprep.workflows.dwi.util import init_dwi_reference_wf
            wf = init_dwi_reference_wf(mem_gb=0.01, omp_nthreads=1)
            wf.inputs.inputnode.b0_ixs=[0]

    Parameters
    ----------
    omp_nthreads : int
        Maximum number of threads an individual process may use
    name : str
        Name of workflow (default: ``dwi_reference_wf``)

    Inputs
    ------
    dwi_file
        dwi NIfTI file
    b0_ixs : list
        index of b0s in dwi NIfTI file

    Outputs
    -------
    dwi_file
        Validated dwi NIfTI file
    raw_ref_image
        Reference image
    ref_image
        Contrast-enhanced reference image
    ref_image_brain
        Skull-stripped reference image
    dwi_mask
        Skull-stripping mask of reference image
    validation_report
        HTML reportlet indicating whether ``dwi_file`` had a valid affine

    See Also
    --------
    * :py:func:`~dmriprep.workflows.dwi.util.init_enhance_and_skullstrip_wf`

    """
    workflow = Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=["dwi_file", "b0_ixs"]), name="inputnode"
    )
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "dwi_file",
                "raw_ref_image",
                "ref_image",
                "ref_image_brain",
                "dwi_mask",
                "validation_report",
            ]
        ),
        name="outputnode",
    )

    validate = pe.Node(ValidateImage(), name="validate", mem_gb=mem_gb)

    extract_b0 = pe.Node(ExtractB0(), name="extract_b0")

    reg_b0 = pe.Node(fsl.MCFLIRT(ref_vol=0, interpolation="sinc"), name="reg_b0")

    pre_mask = pe.Node(afni.Automask(dilate=1, outputtype="NIFTI_GZ"), name="pre_mask")

    rescale_b0 = pe.Node(RescaleB0(), name="rescale_b0")

    enhance_and_skullstrip_dwi_wf = init_enhance_and_skullstrip_dwi_wf(
        omp_nthreads=omp_nthreads
    )

    # fmt:off
    workflow.connect([
        (inputnode, validate, [("dwi_file", "in_file")]),
        (validate, extract_b0, [("out_file", "in_file")]),
        (inputnode, extract_b0, [("b0_ixs", "b0_ixs")]),
        (extract_b0, reg_b0, [("out_file", "in_file")]),
        (reg_b0, pre_mask, [("out_file", "in_file")]),
        (reg_b0, rescale_b0, [("out_file", "in_file")]),
        (pre_mask, rescale_b0, [("out_file", "mask_file")]),
        (rescale_b0, enhance_and_skullstrip_dwi_wf, [("out_ref", "inputnode.in_file")]),
        (pre_mask, enhance_and_skullstrip_dwi_wf, [("out_file", "inputnode.pre_mask")]),
        (validate, outputnode, [("out_file", "dwi_file"), ("out_report", "validation_report")]),
        (rescale_b0, outputnode, [("out_ref", "raw_ref_image")]),
        (enhance_and_skullstrip_dwi_wf, outputnode, [
            ("outputnode.bias_corrected_file", "ref_image"),
            ("outputnode.mask_file", "dwi_mask"),
            ("outputnode.skull_stripped_file", "ref_image_brain"),
        ]),
    ])
    # fmt:on
    return workflow


def init_enhance_and_skullstrip_dwi_wf(
    name="enhance_and_skullstrip_dwi_wf", omp_nthreads=1
):
    """
    Enhance a *b0* reference and perform brain extraction.

    This workflow takes in a *b0* reference image and sharpens the histogram
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

    Workflow Graph:
        .. workflow ::
            :graph2use: orig
            :simple_form: yes

            from dmriprep.workflows.dwi.util import init_enhance_and_skullstrip_dwi_wf
            wf = init_enhance_and_skullstrip_dwi_wf(omp_nthreads=1)

    .. _N4BiasFieldCorrection: https://hdl.handle.net/10380/3053

    Parameters
    ----------
    name : str
        Name of workflow (default: ``enhance_and_skullstrip_dwi_wf``)
    omp_nthreads : int
        number of threads available to parallel nodes

    Inputs
    ------
    in_file
        The *b0* reference (single volume)
    pre_mask
        initial mask

    Outputs
    -------
    bias_corrected_file
        the ``in_file`` after `N4BiasFieldCorrection`_
    skull_stripped_file
        the ``bias_corrected_file`` after skull-stripping
    mask_file
        mask of the skull-stripped input file
    out_report
        reportlet for the skull-stripping

    """
    workflow = Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["in_file", "pre_mask"]), name="inputnode"
    )
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["mask_file", "skull_stripped_file", "bias_corrected_file"]
        ),
        name="outputnode",
    )

    # Run N4 normally, force num_threads=1 for stability (images are small, no need for >1)
    n4_correct = pe.Node(
        N4BiasFieldCorrection(
            dimension=3, copy_header=True, bspline_fitting_distance=200
        ),
        shrink_factor=2,
        name="n4_correct",
        n_procs=1,
    )
    n4_correct.inputs.rescale_intensities = True

    # Create a generous BET mask out of the bias-corrected EPI
    skullstrip_first_pass = pe.Node(
        fsl.BET(frac=0.2, mask=True), name="skullstrip_first_pass"
    )
    bet_dilate = pe.Node(
        fsl.DilateImage(
            operation="max",
            kernel_shape="sphere",
            kernel_size=6.0,
            internal_datatype="char",
        ),
        name="skullstrip_first_dilate",
    )
    bet_mask = pe.Node(fsl.ApplyMask(), name="skullstrip_first_mask")

    # Use AFNI's unifize for T2 contrast & fix header
    unifize = pe.Node(
        afni.Unifize(
            t2=True,
            outputtype="NIFTI_GZ",
            args="-clfrac 0.2 -rbt 18.3 65.0 90.0",
            out_file="uni.nii.gz",
        ),
        name="unifize",
    )
    fixhdr_unifize = pe.Node(CopyXForm(), name="fixhdr_unifize", mem_gb=0.1)

    # Run AFNI's 3dAutomask to extract a refined brain mask
    skullstrip_second_pass = pe.Node(
        afni.Automask(dilate=1, outputtype="NIFTI_GZ"), name="skullstrip_second_pass"
    )
    fixhdr_skullstrip2 = pe.Node(CopyXForm(), name="fixhdr_skullstrip2", mem_gb=0.1)

    # Take intersection of both masks
    combine_masks = pe.Node(fsl.BinaryMaths(operation="mul"), name="combine_masks")

    normalize = pe.Node(niu.Function(function=_normalize), name="normalize")

    # Compute masked brain
    apply_mask = pe.Node(ApplyMask(), name="apply_mask")

    # fmt:off
    workflow.connect([
        (inputnode, n4_correct, [("in_file", "input_image"),
                                 ("pre_mask", "mask_image")]),
        (inputnode, fixhdr_unifize, [("in_file", "hdr_file")]),
        (inputnode, fixhdr_skullstrip2, [("in_file", "hdr_file")]),
        (n4_correct, skullstrip_first_pass, [("output_image", "in_file")]),
        (skullstrip_first_pass, bet_dilate, [("mask_file", "in_file")]),
        (bet_dilate, bet_mask, [("out_file", "mask_file")]),
        (skullstrip_first_pass, bet_mask, [("out_file", "in_file")]),
        (bet_mask, unifize, [("out_file", "in_file")]),
        (unifize, fixhdr_unifize, [("out_file", "in_file")]),
        (fixhdr_unifize, skullstrip_second_pass, [("out_file", "in_file")]),
        (skullstrip_first_pass, combine_masks, [("mask_file", "in_file")]),
        (skullstrip_second_pass, fixhdr_skullstrip2, [("out_file", "in_file")]),
        (fixhdr_skullstrip2, combine_masks, [("out_file", "operand_file")]),
        (combine_masks, apply_mask, [("out_file", "in_mask")]),
        (combine_masks, outputnode, [("out_file", "mask_file")]),
        (n4_correct, normalize, [("output_image", "in_file")]),
        (normalize, apply_mask, [("out", "in_file")]),
        (normalize, outputnode, [("out", "bias_corrected_file")]),
        (apply_mask, outputnode, [("out_file", "skull_stripped_file")]),
    ]
    )
    # fmt:on
    return workflow


def _normalize(in_file, newmax=2000, perc=98.0):
    from pathlib import Path
    import numpy as np
    import nibabel as nb

    nii = nb.load(in_file)
    data = nii.get_fdata()
    data[data < 0] = 0
    if data.max() >= 2 ** 15 - 1:
        data *= newmax / np.percentile(data.reshape(-1), perc)

    out_file = str(Path("normalized.nii.gz").absolute())
    hdr = nii.header.copy()
    hdr.set_data_dtype("int16")
    nii.__class__(data.astype("int16"), nii.affine, hdr).to_filename(out_file)
    return out_file


def gen_index(in_file):
    # Generate the index file for eddy
    import os
    import numpy as np
    import nibabel as nib
    from nipype.pipeline import engine as pe
    from nipype.interfaces import fsl, utility as niu
    from nipype.utils.filemanip import fname_presuffix

    out_file = fname_presuffix(
        in_file,
        suffix="_index.txt",
        newpath=os.path.abspath("."),
        use_ext=False,
    )
    vols = nib.load(in_file).shape[-1]
    index_lines = np.ones((vols,))
    index_lines_reshape = index_lines.reshape(1, index_lines.shape[0])
    np.savetxt(out_file, index_lines_reshape, fmt="%i")
    return out_file

def gen_acqparams(in_file, total_readout_time=0.05):
    # Generate the acqp file for eddy
    import os
    import numpy as np
    import nibabel as nb
    from nipype.utils.filemanip import fname_presuffix

    # Get the metadata for the dwi
    layout = config.execution.layout
    metadata = str(layout.get_metadata(dwi_file))

    # Generate output file name
    out_file = fname_presuffix(
        in_file,
        suffix="_acqparams.txt",
        newpath=os.path.abspath("."),
        use_ext=False,
    )

    # Dictionary for converting directions to acqp lines
    acq_param_dict = {
        "j": "0 1 0 %.7f",
        "j-": "0 -1 0 %.7f",
        "i": "1 0 0 %.7f",
        "i-": "-1 0 0 %.7f",
        "k": "0 0 1 %.7f",
        "k-": "0 0 -1 %.7f",
    }

    # Get encoding direction from json
    if metadata.get("PhaseEncodingDirection"):
        pe_dir = metadata.get("PhaseEncodingDirection")
    else:
        pe_dir = metadata.get("PhaseEncodingAxis")

    # Get readout time from json, use default of 0.05 otherwise
    if metadata.get("TotalReadoutTime"):
        total_readout = metadata.get("TotalReadoutTime")
    else:
        total_readout = total_readout_time

    # Construct the acqp file lines
    acq_param_lines = acq_param_dict[pe_dir] % total_readout

    # Write to the acqp file
    with open(out_file, "w") as f:
        f.write(acq_param_lines)

    return out_file


def init_eddy_wf(
        name="eddy_wf",
    ):
    """
    Create an eddy workflow for head motion distortion correction on the dwi.

    Parameters
    ----------
    name : str
        Name of workflow (default: ``eddy_wf``)

    Inputs
    ----------
    dwi_file
        dwi NIfTI file
    dwi_mask
        Skull-stripping mask of reference image
    in_bvec
        File containing bvecs of dwi
    in_bval
        File containing bvals of dwi
    
    Outputs
    -------
    out_eddy :
        The eddy corrected diffusion image.
    out_rotated_bvecs :
        Rotated bvecs for each volume after eddy.
    """
    from nipype.interfaces.fsl import ApplyMask, Eddy, EddyQuad

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "dwi_file",
                "dwi_mask",
                "in_bvec",
                "in_bval",
            ]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "out_eddy",
                "out_rotated_bvecs"
            ]
        ),
        name="outputnode",
    )

    workflow = Workflow(name=name)

    eddy = pe.Node(
        Eddy(repol=True, cnr_maps=True, residuals=True, method="jac"),
        name="fsl_eddy",
    )

    # Generate the acqp file for eddy
    eddy_acqp = pe.Node(
        niu.Function(
            input_names=["in_file"],
            output_names=["out_file"],
            function=gen_acqparams,
        ),
        name="eddy_acqp",
    )

    # Generate the index file for eddy
    gen_idx = pe.Node(
        niu.Function(
            input_names=["in_file"],
            output_names=["out_file"],
            function=gen_index,
        ),
        name="gen_index",
    )

    eddy_quad = pe.Node(EddyQuad(verbose=True), name="eddy_quad")

    # Connect the workflow
    # fmt:off
    workflow.connect([
        (inputnode, eddy, [
            ("dwi_file", "in_file"),
            ("dwi_mask", "in_mask"),
            ("in_bvec", "in_bvec"),
            ("in_bval", "in_bval"),
        ]),
        (eddy_acqp, eddy, [("out_file", "in_acqp")]),
        (gen_idx, eddy, [("out_file", "in_index")]),
        # Eddy Quad Outputs
        (inputnode, eddy_quad, [
            ("dwi_mask", "mask_file"),
            ("in_bval", "bval_file"),
        ]),
        (eddy, eddy_quad, [("out_rotated_bvecs", "bvec_file")]),
        (eddy_acqp, eddy_quad, [("out_file", "param_file")]),
        (gen_idx, eddy_quad, [("out_file", "idx_file")]),
        (eddy, outputnode, [
            ("out_corrected", "out_eddy"),
            ("out_rotated_bvecs", "out_rotated_bvecs")
        ]),
    ])
    # fmt:on
    return workflow