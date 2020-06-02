"""Orchestrating the dMRI-preprocessing workflow."""
from ... import config
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from ...interfaces.vectors import CheckGradientTable
from .util import init_dwi_reference_wf
from .outputs import init_reportlets_wf


def init_early_b0ref_wf(
    name="early_b0ref_wf",
):
    """
    Build an early :math:`b = 0` average reference for internal consumption of *dMRIPrep*.

    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes

            from dmriprep.config.testing import mock_config
            from dmriprep import config
            from dmriprep.workflows.dwi.base import init_early_b0ref_wf
            with mock_config():
                wf = init_early_b0ref_wf()

    Inputs
    ------
    dwi_file
        dwi NIfTI file
    in_bvec
        File path of the b-vectors
    in_bval
        File path of the b-values

    Outputs
    -------
    dwi_reference
        A 3D :math:`b = 0` reference, before susceptibility distortion correction.
    dwi_mask
        A 3D, binary mask of the ``dwi_reference`` above.
    gradients_rasb
        A *RASb* (RAS+ coordinates, scaled b-values, normalized b-vectors, BIDS-compatible)
        gradient table.

    See Also
    --------
    * :py:func:`~dmriprep.workflows.dwi.util.init_dwi_reference_wf`
    * :py:func:`~dmriprep.workflows.dwi.outputs.init_reportlets_wf`

    """
    # Build workflow
    workflow = Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['dwi_file', 'in_bvec', 'in_bval']),
        name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['dwi_reference', 'dwi_mask', 'gradients_rasb']),
        name='outputnode')

    gradient_table = pe.Node(CheckGradientTable(), name='gradient_table')

    dwi_reference_wf = init_dwi_reference_wf(
        mem_gb=config.DEFAULT_MEMORY_MIN_GB,
        omp_nthreads=config.nipype.omp_nthreads)

    # MAIN WORKFLOW STRUCTURE
    workflow.connect([
        (inputnode, gradient_table, [
            ('dwi_file', 'dwi_file'),
            ('in_bvec', 'in_bvec'),
            ('in_bval', 'in_bval')]),
        (inputnode, dwi_reference_wf, [('dwi_file', 'inputnode.dwi_file')]),
        (gradient_table, dwi_reference_wf, [('b0_ixs', 'inputnode.b0_ixs')]),
        (dwi_reference_wf, outputnode, [
            ('outputnode.ref_image', 'dwi_reference'),
            ('outputnode.dwi_mask', 'dwi_mask')]),
        (gradient_table, outputnode, [('out_rasb', 'gradients_rasb')])
    ])

    # REPORTING ############################################################
    reportlets_wf = init_reportlets_wf(str(config.execution.output_dir))
    workflow.connect([
        (inputnode, reportlets_wf, [('dwi_file', 'inputnode.source_file')]),
        (dwi_reference_wf, reportlets_wf, [
            ('outputnode.ref_image', 'inputnode.dwi_ref'),
            ('outputnode.dwi_mask', 'inputnode.dwi_mask'),
            ('outputnode.validation_report', 'inputnode.validation_report')]),
    ])
    return workflow
