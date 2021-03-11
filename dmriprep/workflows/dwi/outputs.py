"""Write outputs (derivatives and reportlets)."""
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from ...interfaces import DerivativesDataSink


def init_reportlets_wf(output_dir, sdc_report=False, name="reportlets_wf"):
    """Set up a battery of datasinks to store reports in the right location."""
    from niworkflows.interfaces.reportlets.masks import SimpleShowMaskRPT

    workflow = Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "source_file",
                "summary_report",
                "dwi_ref",
                "dwi_mask",
                "validation_report",
                "sdc_report",
            ]
        ),
        name="inputnode",
    )

    ds_report_summary = pe.Node(
        DerivativesDataSink(
            base_directory=output_dir, desc="summary", datatype="figures"
        ),
        name="ds_report_summary",
        run_without_submitting=True,
    )

    mask_reportlet = pe.Node(SimpleShowMaskRPT(), name="mask_reportlet")

    ds_report_mask = pe.Node(
        DerivativesDataSink(
            base_directory=output_dir, desc="brain", suffix="mask", datatype="figures"
        ),
        name="ds_report_mask",
        run_without_submitting=True,
    )
    ds_report_validation = pe.Node(
        DerivativesDataSink(
            base_directory=output_dir, desc="validation", datatype="figures"
        ),
        name="ds_report_validation",
        run_without_submitting=True,
    )

    # fmt:off
    workflow.connect([
        (inputnode, ds_report_summary, [("source_file", "source_file"),
                                        ("summary_report", "in_file")]),
        (inputnode, mask_reportlet, [("dwi_ref", "background_file"),
                                     ("dwi_mask", "mask_file")]),
        (inputnode, ds_report_validation, [("source_file", "source_file"),
                                           ("validation_report", "in_file")]),
        (inputnode, ds_report_mask, [("source_file", "source_file")]),
        (mask_reportlet, ds_report_mask, [("out_report", "in_file")]),
    ])
    # fmt:on
    if sdc_report:
        ds_report_sdc = pe.Node(
            DerivativesDataSink(
                base_directory=output_dir, desc="sdc", suffix="dwi", datatype="figures"
            ),
            name="ds_report_sdc",
            run_without_submitting=True,
        )
        # fmt:off
        workflow.connect([
            (inputnode, ds_report_sdc, [("source_file", "source_file"),
                                        ("sdc_report", "in_file")]),
        ])
        # fmt:on
    return workflow
