"""Orchestrating the dMRI-preprocessing workflow."""
from ... import config
from pathlib import Path
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from ...interfaces import DerivativesDataSink


def init_dwi_preproc_wf(dwi_file, has_fieldmap=False):
    """
    Build a preprocessing workflow for one DWI run.

    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes

            from dmriprep.config.testing import mock_config
            from dmriprep import config
            from dmriprep.workflows.dwi.base import init_dwi_preproc_wf
            with mock_config():
                wf = init_dwi_preproc_wf(
                    f"{config.execution.layout.root}/"
                    "sub-THP0005/dwi/sub-THP0005_dwi.nii.gz"
                )

    Parameters
    ----------
    dwi_file : :obj:`os.PathLike`
        One diffusion MRI dataset to be processed.
    has_fieldmap : :obj:`bool`
        Build the workflow with a path to register a fieldmap to the DWI.

    Inputs
    ------
    dwi_file
        dwi NIfTI file
    in_bvec
        File path of the b-vectors
    in_bval
        File path of the b-values
    fmap
        File path of the fieldmap
    fmap_ref
        File path of the fieldmap reference
    fmap_coeff
        File path of the fieldmap coefficients
    fmap_mask
        File path of the fieldmap mask
    fmap_id
        The BIDS modality label of the fieldmap being used


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
    from ...interfaces.vectors import CheckGradientTable
    from .util import init_dwi_reference_wf
    from .outputs import init_reportlets_wf

    layout = config.execution.layout

    dwi_file = Path(dwi_file)
    config.loggers.workflow.debug(
        f"Creating DWI preprocessing workflow for <{dwi_file.name}>"
    )

    # Build workflow
    workflow = Workflow(name=_get_wf_name(dwi_file.name))

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                # DWI
                "dwi_file",
                "in_bvec",
                "in_bval",
                # From SDCFlows
                "fmap",
                "fmap_ref",
                "fmap_coeff",
                "fmap_mask",
                "fmap_id",
                # From anatomical
                "t1w_preproc",
                "t1w_mask",
                "t1w_dseg",
                "t1w_aseg",
                "t1w_aparc",
                "t1w_tpms",
                "template",
                "anat2std_xfm",
                "std2anat_xfm",
                "subjects_dir",
                "subject_id",
                "t1w2fsnative_xfm",
                "fsnative2t1w_xfm",
            ]
        ),
        name="inputnode",
    )
    inputnode.inputs.dwi_file = str(dwi_file.absolute())
    inputnode.inputs.in_bvec = str(layout.get_bvec(dwi_file))
    inputnode.inputs.in_bval = str(layout.get_bval(dwi_file))

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["dwi_reference", "dwi_mask", "gradients_rasb"]),
        name="outputnode",
    )

    gradient_table = pe.Node(CheckGradientTable(), name="gradient_table")

    dwi_reference_wf = init_dwi_reference_wf(
        mem_gb=config.DEFAULT_MEMORY_MIN_GB, omp_nthreads=config.nipype.omp_nthreads
    )

    # MAIN WORKFLOW STRUCTURE
    # fmt: off
    workflow.connect([
        (inputnode, gradient_table, [("dwi_file", "dwi_file"),
                                     ("in_bvec", "in_bvec"),
                                     ("in_bval", "in_bval")]),
        (inputnode, dwi_reference_wf, [("dwi_file", "inputnode.dwi_file")]),
        (gradient_table, dwi_reference_wf, [("b0_ixs", "inputnode.b0_ixs")]),
        (gradient_table, outputnode, [("out_rasb", "gradients_rasb")]),
    ])
    # fmt: on

    if config.workflow.run_reconall:
        from niworkflows.interfaces.nibabel import ApplyMask
        from niworkflows.anat.coregistration import init_bbreg_wf
        from ...utils.misc import sub_prefix as _prefix

        # Mask the T1w
        t1w_brain = pe.Node(ApplyMask(), name="t1w_brain")

        bbr_wf = init_bbreg_wf(
            debug=config.execution.debug,
            epi2t1w_init=config.workflow.dwi2t1w_init,
            omp_nthreads=config.nipype.omp_nthreads,
        )

        ds_report_reg = pe.Node(
            DerivativesDataSink(
                base_directory=str(config.execution.output_dir),
                datatype="figures",
            ),
            name="ds_report_reg",
            run_without_submitting=True,
        )

        def _bold_reg_suffix(fallback):
            return "coreg" if fallback else "bbregister"

        # fmt: off
        workflow.connect([
            (inputnode, bbr_wf, [
                ("fsnative2t1w_xfm", "inputnode.fsnative2t1w_xfm"),
                (("subject_id", _prefix), "inputnode.subject_id"),
                ("subjects_dir", "inputnode.subjects_dir"),
            ]),
            # T1w Mask
            (inputnode, t1w_brain, [("t1w_preproc", "in_file"),
                                    ("t1w_mask", "in_mask")]),
            (inputnode, ds_report_reg, [("dwi_file", "source_file")]),
            # BBRegister
            (dwi_reference_wf, bbr_wf, [
                ("outputnode.ref_image", "inputnode.in_file")
            ]),
            (bbr_wf, ds_report_reg, [
                ('outputnode.out_report', 'in_file'),
                (('outputnode.fallback', _bold_reg_suffix), 'desc')]),
        ])
        # fmt: on

    # REPORTING ############################################################
    reportlets_wf = init_reportlets_wf(str(config.execution.output_dir))
    # fmt: off
    workflow.connect([
        (inputnode, reportlets_wf, [("dwi_file", "inputnode.source_file")]),
        (dwi_reference_wf, reportlets_wf, [
            ("outputnode.validation_report", "inputnode.validation_report"),
        ]),
        (outputnode, reportlets_wf, [
            ("dwi_reference", "inputnode.dwi_ref"),
            ("dwi_mask", "inputnode.dwi_mask"),
        ]),
    ])
    # fmt: on

    if not has_fieldmap:
        # fmt: off
        workflow.connect([
            (dwi_reference_wf, outputnode, [("outputnode.ref_image", "dwi_reference"),
                                            ("outputnode.dwi_mask", "dwi_mask")]),
        ])
        # fmt: on
        return workflow

    from niworkflows.interfaces.utility import KeySelect
    from sdcflows.workflows.apply.registration import init_coeff2epi_wf
    from sdcflows.workflows.apply.correction import init_unwarp_wf

    # TODO: Requires nipreps/sdcflows#148
    # from sdcflows.utils.fieldmap import get_identifier

    coeff2epi_wf = init_coeff2epi_wf(
        omp_nthreads=config.nipype.omp_nthreads, write_coeff=True
    )
    unwarp_wf = init_unwarp_wf(omp_nthreads=config.nipype.omp_nthreads)
    unwarp_wf.inputs.inputnode.metadata = layout.get_metadata(str(dwi_file))

    output_select = pe.Node(
        KeySelect(fields=["fmap", "fmap_ref", "fmap_coeff", "fmap_mask"]),
        name="output_select",
        run_without_submitting=True,
    )
    # estimator_key = get_identifier(dwi_file)
    # if len(estimator_key) != 1:
    #     raise RuntimeError(
    #         f"Incorrect number of fieldmap estimator IDs ({len(estimator_key)})."
    #     )
    # output_select.inputs.key = estimator_key

    # fmt: off
    workflow.connect([
        (inputnode, output_select, [("fmap", "fmap"),
                                    ("fmap_ref", "fmap_ref"),
                                    ("fmap_coeff", "fmap_coeff"),
                                    ("fmap_mask", "fmap_mask"),
                                    ("fmap_id", "keys")]),
        (output_select, coeff2epi_wf, [
            ("fmap_ref", "inputnode.fmap_ref"),
            ("fmap_coeff", "inputnode.fmap_coeff"),
            ("fmap_mask", "inputnode.fmap_mask")]),
        (dwi_reference_wf, coeff2epi_wf, [
            ("outputnode.ref_image", "inputnode.target_ref"),
            ("outputnode.dwi_mask", "inputnode.target_mask")]),
        (dwi_reference_wf, unwarp_wf, [("outputnode.ref_image", "inputnode.distorted")]),
        (coeff2epi_wf, unwarp_wf, [
            ("outputnode.fmap_coeff", "inputnode.fmap_coeff")]),
        (unwarp_wf, outputnode, [("outputnode.corrected", "dwi_reference")]),
    ])
    # fmt: on

    return workflow


def _get_wf_name(filename):
    """
    Derive the workflow name for supplied DWI file.

    Examples
    --------
    >>> _get_wf_name('/completely/made/up/path/sub-01_dir-AP_acq-64grad_dwi.nii.gz')
    'dwi_preproc_dir_AP_acq_64grad_wf'

    >>> _get_wf_name('/completely/made/up/path/sub-01_dir-RL_run-01_echo-1_dwi.nii.gz')
    'dwi_preproc_dir_RL_run_01_echo_1_wf'

    """
    from pathlib import Path

    fname = Path(filename).name.rpartition(".nii")[0].replace("_dwi", "_wf")
    fname_nosub = "_".join(fname.split("_")[1:])
    return f"dwi_preproc_{fname_nosub.replace('.', '_').replace(' ', '').replace('-', '_')}"
