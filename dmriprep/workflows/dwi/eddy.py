"""
Eddy-currents and head-motion estimation/correction.

.. testsetup::
    >>> tmpdir = getfixture('tmpdir')
    >>> tmp = tmpdir.chdir() # changing to a temporary directory
    >>> nb.Nifti1Image(np.zeros((90, 90, 60, 6)), None, None).to_filename(
    ...     tmpdir.join('dwi.nii.gz').strpath)

"""
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from niworkflows.engine.workflows import LiterateWorkflow as Workflow


def gen_eddy_textfiles(in_file, in_meta):
    """
    Generate the acquisition-parameters and index files for FSL ``eddy_openmp``.

    Examples
    --------
    >>> out_acqparams, out_index = gen_eddy_textfiles(
    ...     "dwi.nii.gz",
    ...     {"PhaseEncodingDirection": "j-", "TotalReadoutTime": 0.005},
    ... )
    >>> Path(out_acqparams).read_text()
    '0 -1 0 0.0050000'

    >>> Path(out_index).read_text()
    '1 1 1 1 1 1'

    """
    from pathlib import Path
    import nibabel as nb
    from sdcflows.utils.epimanip import get_trt
    from nipype.utils.filemanip import fname_presuffix

    # Generate output file name
    out_acqparams = fname_presuffix(
        in_file,
        suffix="_acqparams.txt",
        use_ext=False,
    )

    pe_dir = in_meta["PhaseEncodingDirection"]
    fsl_pe = ["0"] * 3
    fsl_pe["ijk".index(pe_dir[0])] = "-1" if pe_dir.endswith("-") else "1"

    # Write to the acqp file
    try:
        Path(out_acqparams).write_text(
            f"{' '.join(fsl_pe)} {get_trt(in_meta, in_file=in_file):0.7f}"
        )
    except ValueError:
        Path(out_acqparams).write_text(f"{' '.join(fsl_pe)} {0.05}")

    out_index = fname_presuffix(
        in_file,
        suffix="_index.txt",
        use_ext=False,
    )
    Path(out_index).write_text(f"{' '.join(['1'] * nb.load(in_file).shape[3])}")
    return out_acqparams, out_index


def init_eddy_wf(debug=False, name="eddy_wf"):
    """
    Create a workflow for head-motion & Eddy currents distortion estimation with FSL.

    Parameters
    ----------
    name : :obj:`str`
        Name of workflow (default: ``eddy_wf``)

    Inputs
    ------
    dwi_file
        dwi NIfTI file

    Outputs
    -------
    out_eddy
        The eddy corrected diffusion image..

    """
    from nipype.interfaces.fsl import Eddy, ExtractROI

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=["dwi_file", "metadata", "dwi_mask", "in_bvec", "in_bval"]
        ),
        name="inputnode",
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["out_rotated_bvecs", "eddy_ref_image", "out_eddy"]
        ),
        name="outputnode",
    )

    workflow = Workflow(name=name)
    workflow.__desc__ = f"""\
Geometrical distortions derived from the so-called Eddy-currents, and head-motion
realignment parameters were estimated with the joint modeling of ``eddy_openmp``,
included in FSL {Eddy().version} [@eddy].
"""
    eddy = pe.Node(
        Eddy(),
        name="eddy",
    )

    if debug:
        eddy.inputs.niter = 1
        eddy.inputs.is_shelled = True
        eddy.inputs.dont_peas = True
        eddy.inputs.nvoxhp = 100

    # Generate the acqp and index files for eddy
    gen_eddy_files = pe.Node(
        niu.Function(
            input_names=["in_file", "in_meta"],
            output_names=["out_acqparams", "out_index"],
            function=gen_eddy_textfiles,
        ),
        name="gen_eddy_files",
    )

    eddy_ref_img = pe.Node(ExtractROI(t_min=0, t_size=1), name="eddy_roi")

    # fmt:off
    workflow.connect([
        (inputnode, eddy, [
            ("dwi_file", "in_file"),
            ("dwi_mask", "in_mask"),
            ("in_bvec", "in_bvec"),
            ("in_bval", "in_bval"),
        ]),
        (inputnode, gen_eddy_files, [
            ("dwi_file", "in_file"),
            ("metadata", "in_meta")
        ]),
        (gen_eddy_files, eddy, [
            ("out_acqparams", "in_acqp"),
            ("out_index", "in_index"),
        ]),
        (eddy, outputnode, [
            ("out_corrected", "out_eddy"),
            ("out_rotated_bvecs", "out_rotated_bvecs")
        ]),
        (eddy, eddy_ref_img, [("out_corrected", "in_file")]),
        (eddy_ref_img, outputnode, [("roi_file", "eddy_ref_image")]),
    ])
    # fmt:on
    return workflow
