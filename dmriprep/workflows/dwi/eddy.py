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
    out_acqparams = fname_presuffix(in_file, suffix="_acqparams.txt", use_ext=False,)

    pe_dir = in_meta["PhaseEncodingDirection"]
    fsl_pe = ["0"] * 3
    fsl_pe["ijk".index(pe_dir[0])] = "-1" if pe_dir.endswith("-") else "1"

    # Write to the acqp file
    Path(out_acqparams).write_text(
        f"{' '.join(fsl_pe)} {get_trt(in_meta, in_file=in_file):0.7f}"
    )

    out_index = fname_presuffix(in_file, suffix="_index.txt", use_ext=False,)
    Path(out_index).write_text(f"{' '.join(['1'] * nb.load(in_file).shape[3])}")
    return out_acqparams, out_index


def init_eddy_wf(name="eddy_wf"):
    """
    Create a workflow for head-motion & Eddy currents distortion estimation with FSL.

    Parameters
    ----------
    name : :obj:`str`
        Name of workflow (default: ``eddy_wf``)

    Inputs
    ----------
    dwi_file
        dwi NIfTI file

    Outputs
    -------
    out_eddy :
        The eddy corrected diffusion image..

    """
    from nipype.interfaces.fsl import EddyCorrect

    inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_file"]), name="inputnode",)

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_eddy"]), name="outputnode",)

    workflow = Workflow(name=name)
    workflow.__desc__ = f"""\
Geometrical distortions derived from the so-called Eddy-currents, and head-motion
realignment parameters were estimated with the joint modeling of FSL ``eddy_correct``
included in FSL {EddyCorrect().version} [@eddy].
"""

    eddy_correct = pe.Node(EddyCorrect(), name="eddy_correct",)

    # Connect the workflow
    # fmt:off
    workflow.connect([
        (inputnode, eddy_correct, [("dwi_file", "in_file")]),
        (eddy_correct, outputnode, [("eddy_corrected", "out_eddy")]),
    ])
    # fmt:on
    return workflow
