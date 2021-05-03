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
                "dwi_ref",
                "dwi_mask",
                "validation_report",
                "sdc_report",
            ]
        ),
        name="inputnode",
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
        (inputnode, mask_reportlet, [("dwi_ref", "background_file"),
                                     ("dwi_mask", "mask_file")]),
        (inputnode, ds_report_validation, [("source_file", "source_file")]),
        (inputnode, ds_report_mask, [("source_file", "source_file")]),
        (inputnode, ds_report_validation, [("validation_report", "in_file")]),
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


def init_dwi_derivatives_wf(output_dir, name="dwi_derivatives_wf"):
    """
    Set up a battery of datasinks to store dwi derivatives in the right location.

    Parameters
    ----------
    output_dir : :obj:`str`
        Directory in which to save derivatives.
    name : :obj:`str`
        Workflow name (default: ``"dwi_derivatives_wf"``).

    Inputs
    ------
    source_file
        One dwi file that will serve as a file naming reference.
    dwi_ref
        The b0 reference.
    dwi_mask
        The brain mask for the dwi file.

    """
    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["source_file", "dwi_ref", "dwi_mask"]),
        name="inputnode",
    )

    ds_reference = pe.Node(
        DerivativesDataSink(
            base_directory=output_dir,
            compress=True,
            space="dwi",
            suffix="epiref",
            datatype="dwi",
        ),
        name="ds_reference",
    )

    ds_mask = pe.Node(
        DerivativesDataSink(
            base_directory=output_dir,
            compress=True,
            space="dwi",
            desc="brain",
            suffix="mask",
            datatype="dwi",
        ),
        name="ds_mask",
    )

    # fmt:off
    workflow.connect([
        (inputnode, ds_reference, [("source_file", "source_file"),
                                   ("dwi_ref", "in_file")]),
        (inputnode, ds_mask, [("source_file", "source_file"),
                              ("dwi_mask", "in_file")]),
    ])
    # fmt:on

    return workflow
