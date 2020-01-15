"""Orchestrating the dMRI-preprocessing workflow."""
from nipype import logging
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from ...interfaces.vectors import CheckGradientTable
from .util import init_dwi_reference_wf
from .outputs import init_reportlets_wf


LOGGER = logging.getLogger('nipype.workflow')


def init_dwi_preproc_wf(
    dwi_file,
    debug,
    force_syn,
    ignore,
    low_mem,
    omp_nthreads,
    output_dir,
    reportlets_dir,
    use_syn,
    layout=None,
    num_dwi=1,
):
    """
    This workflow controls the diffusion preprocessing stages of *dMRIPrep*.

    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes

            from dmriprep.workflows.dwi import init_dwi_preproc_wf
            from collections import namedtuple
            BIDSLayout = namedtuple('BIDSLayout', ['root'])
            wf = init_dwi_preproc_wf(
                dwi_file='/completely/made/up/path/sub-01_dwi.nii.gz',
                debug=False,
                force_syn=True,
                ignore=[],
                low_mem=False,
                omp_nthreads=1,
                output_dir='.',
                reportlets_dir='.',
                use_syn=True,
                layout=BIDSLayout('.'),
                num_dwi=1,
            )

    Parameters
    ----------
    dwi_file : str
        dwi NIfTI file
    debug : bool
        Enable debugging outputs
    force_syn : bool
        **Temporary**: Always run SyN-based SDC
    ignore : list
        Preprocessing steps to skip (may include "sdc")
    low_mem : bool
        Write uncompressed .nii files in some cases to reduce memory usage
    omp_nthreads : int
        Maximum number of threads an individual process may use
    output_dir : str
        Directory in which to save derivatives
    reportlets_dir : str
        Absolute path of a directory in which reportlets will be temporarily stored
    use_syn : bool
        **Experimental**: Enable ANTs SyN-based susceptibility distortion correction (SDC).
        If fieldmaps are present and enabled, this is not run, by default.
    layout : BIDSLayout
        BIDSLayout structure to enable metadata retrieval
    num_dwi : int
        Total number of dwi files that have been set for preprocessing
        (default is 1)

    Inputs
    ------
    dwi_file
        dwi NIfTI file
    bvec_file
        File path of the b-values
    bval_file
        File path of the b-vectors

    Outputs
    -------
    dwi_file
        dwi NIfTI file
    dwi_mask
        dwi mask

    See also
    --------
    * :py:func:`~dmriprep.workflows.dwi.util.init_dwi_reference_wf`
    * :py:func:`~dmriprep.workflows.dwi.outputs.init_reportlets_wf`

    """
    wf_name = _get_wf_name(dwi_file)

    # Build workflow
    workflow = Workflow(name=wf_name)
    workflow.__desc__ = """

Diffusion data preprocessing

: For each of the {num_dwi} dwi scans found per subject (across all sessions),
 the following preprocessing was performed.
""".format(num_dwi=num_dwi)

    workflow.__postdesc__ = """\
    """

    # For doc building purposes
    if not hasattr(layout, 'parse_file_entities'):
        LOGGER.log(25, 'No valid layout: building empty workflow.')
        bvec_file = '/completely/made/up/path/sub-01_dwi.bvec'
        bval_file = '/completely/made/up/path/sub-01_dwi.bval'
    else:
        bvec_file = layout.get_bvec(dwi_file)
        bval_file = layout.get_bval(dwi_file)

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['dwi_file', 'bvec_file', 'bval_file',
                'subjects_dir', 'subject_id',
                't1w_preproc', 't1w_brain', 't1w_mask', 't1w_dseg', 't1w_tpms',
                't1w_aseg', 't1w_aparc', 'anat2std_xfm', 'std2anat_xfm', 'template',
                'joint_anat2std_xfm', 'joint_std2anat_xfm', 'joint_template',
                't1w2fsnative_xfm', 'fsnative2t1w_xfm']),
        name='inputnode')
    inputnode.inputs.dwi_file = dwi_file
    inputnode.inputs.bvec_file = bvec_file
    inputnode.inputs.bval_file = bval_file

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_dwi', 'out_bvec', 'out_bval', 'out_rasb',
                'out_dwi_mask']),
        name='outputnode')

    gradient_table = pe.Node(CheckGradientTable(), name='gradient_table')

    dwi_reference_wf = init_dwi_reference_wf(omp_nthreads=1)

    # MAIN WORKFLOW STRUCTURE
    workflow.connect([
        (inputnode, gradient_table, [
            ('dwi_file', 'dwi_file'),
            ('bvec_file', 'in_bvec'),
            ('bval_file', 'in_bval')]),
        (inputnode, dwi_reference_wf, [('dwi_file', 'inputnode.dwi_file')]),
        (gradient_table, dwi_reference_wf, [('b0_ixs', 'inputnode.b0_ixs')]),
        (dwi_reference_wf, outputnode, [
            ('outputnode.ref_image', 'out_dwi'),
            ('outputnode.dwi_mask', 'out_dwi_mask')]),
        (gradient_table, outputnode, [
            ('out_bvec', 'out_bvec'),
            ('out_bval', 'out_bval'),
            ('out_rasb', 'out_rasb')])
    ])

    # REPORTING
    reportlets_wf = init_reportlets_wf(reportlets_dir)
    workflow.connect([
        (inputnode, reportlets_wf, [('dwi_file', 'inputnode.source_file')]),
        (dwi_reference_wf, reportlets_wf, [
            ('outputnode.ref_image', 'inputnode.dwi_ref'),
            ('outputnode.dwi_mask', 'inputnode.dwi_mask'),
            ('outputnode.validation_report', 'inputnode.validation_report')]),
    ])
    return workflow


def _get_wf_name(dwi_fname):
    """
    Derive the workflow name for supplied dwi file.

    >>> _get_wf_name('/completely/made/up/path/sub-01_dwi.nii.gz')
    'dwi_preproc_wf'
    >>> _get_wf_name('/completely/made/up/path/sub-01_run-1_dwi.nii.gz')
    'dwi_preproc_run_1_wf'

    """
    from nipype.utils.filemanip import split_filename
    fname = split_filename(dwi_fname)[1]
    fname_nosub = '_'.join(fname.split("_")[1:])
    name = "dwi_preproc_" + fname_nosub.replace(
        ".", "_").replace(" ", "").replace("-", "_").replace("dwi", "wf")

    return name
