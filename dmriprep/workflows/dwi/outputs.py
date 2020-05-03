"""Write outputs (derivatives and reportlets)."""
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from ...interfaces import DerivativesDataSink


def init_reportlets_wf(output_dir, name='reportlets_wf'):
    """Set up a battery of datasinks to store reports in the right location."""
    from niworkflows.interfaces.masks import SimpleShowMaskRPT
    workflow = Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['source_file', 'dwi_ref', 'dwi_mask',
                'validation_report']),
        name='inputnode')
    mask_reportlet = pe.Node(SimpleShowMaskRPT(), name='mask_reportlet')

    ds_report_mask = pe.Node(
        DerivativesDataSink(base_directory=output_dir, desc='brain', suffix='mask',
                            datatype="figures"),
        name='ds_report_mask', run_without_submitting=True)
    ds_report_validation = pe.Node(
        DerivativesDataSink(base_directory=output_dir, desc='validation', datatype="figures"),
        name='ds_report_validation', run_without_submitting=True)

    workflow.connect([
        (inputnode, mask_reportlet, [('dwi_ref', 'background_file'),
                                     ('dwi_mask', 'mask_file')]),
        (inputnode, ds_report_validation, [('source_file', 'source_file')]),
        (inputnode, ds_report_mask, [('source_file', 'source_file')]),
        (inputnode, ds_report_validation, [('validation_report', 'in_file')]),
        (mask_reportlet, ds_report_mask, [('out_report', 'in_file')]),
    ])
    return workflow
