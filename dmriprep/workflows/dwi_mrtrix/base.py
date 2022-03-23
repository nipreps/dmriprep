# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright 2021 The NiPreps Developers <nipreps@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#
"""Orchestrating the dMRI-preprocessing workflow."""
from pathlib import Path

from dmriprep import config
from dmriprep.interfaces import DerivativesDataSink
from dmriprep.workflows.dwi_mrtrix.pipelines.apply_transform.apply_transform import (
    init_apply_transform,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.conversions.nii_conversions.conversion import (
    init_nii_conversion_wf,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.derivatives.derivatives import (
    init_derivatives_wf,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.epi_ref.epi_ref import (
    init_epi_ref_wf,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.epi_reg.epi_reg import (
    init_epireg_wf,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.pre_sdc.pre_sdc import (
    init_phasediff_wf,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.preprocess.preprocess import (
    init_preprocess_wf,
)
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe
from niworkflows.engine.workflows import LiterateWorkflow as Workflow


def init_dwi_preproc_wf(dwi_file):
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
    * :py:func:`~dmriprep.workflows.dwi.outputs.init_dwi_derivatives_wf`
    * :py:func:`~dmriprep.workflows.dwi.outputs.init_reportlets_wf`

    """
    from dmriprep.workflows.dwi_mrtrix.pipelines.conversions import (
        init_mif_conversion_wf,
    )
    from dmriprep.workflows.dwi_mrtrix.utils.bids import locate_associated_file
    from niworkflows.interfaces.nibabel import ApplyMask
    from niworkflows.interfaces.reportlets.registration import (
        SimpleBeforeAfterRPT as SimpleBeforeAfter,
    )
    from niworkflows.workflows.epi.refmap import init_epi_reference_wf
    from sdcflows.workflows.ancillary import init_brainextraction_wf

    from ...interfaces.vectors import CheckGradientTable
    from .eddy import init_eddy_wf
    from .outputs import init_dwi_derivatives_wf, init_reportlets_wf

    layout = config.execution.layout
    dwi_file = Path(dwi_file)
    config.loggers.workflow.debug(
        f"Creating DWI preprocessing workflow for <{dwi_file.name}>"
    )
    corresponding_fieldmaps = layout.get_fieldmap(dwi_file, return_list=True)
    if not corresponding_fieldmaps:
        has_fieldmap = False
        config.loggers.workflow.critical(
            f"None of the available fieldmaps are associated to <{dwi_file.name}>"
        )
    else:
        #: TODO: Make more robust! currently only matches PEPOLAR scheme.
        has_fieldmap = True
        if len(corresponding_fieldmaps) > 1:
            config.loggers.workflow.critical(
                f"""More than one available fieldmaps are associated to <{dwi_file.name}>.
            Only PEPOLAR scheme is currently supported: using first available fieldmap."""
            )
        fmap = Path(corresponding_fieldmaps[0].get("epi"))

    # Build workflow
    workflow = Workflow(name=_get_wf_name(dwi_file.name))

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                # DWI
                "dwi_file",
                "in_bvec",
                "in_bval",
                "dwi_json",
                # Fieldmap -
                #: TODO: Make more robust! currently only matches PEPOLAR scheme.
                "fmap_file",
                "fmap_json",
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
    inputnode.inputs.dwi_json = str(
        locate_associated_file(layout, dwi_file.absolute())
    )
    inputnode.inputs.fmap_file = fmap
    inputnode.inputs.fmap_json = str(
        locate_associated_file(layout, fmap.absolute())
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=["dwi_reference", "dwi_mask", "gradients_rasb"]
        ),
        name="outputnode",
    )
    mif_conversion_wf = init_mif_conversion_wf()
    nii_conversion_wf = init_nii_conversion_wf()
    brainextraction_wf = init_brainextraction_wf()
    workflow.connect(
        [
            (
                inputnode,
                mif_conversion_wf,
                [
                    ("dwi_file", "inputnode.dwi_file"),
                    ("in_bvec", "inputnode.in_bvec"),
                    ("in_bval", "inputnode.in_bval"),
                    ("dwi_json", "inputnode.dwi_json"),
                    ("fmap_file", "inputnode.fmap_file"),
                    ("fmap_json", "inputnode.fmap_json"),
                ],
            )
        ]
    )
    epi_ref_wf = init_epi_ref_wf()
    apply_transform_wf = init_apply_transform()
    # Mask the T1w
    t1w_brain = pe.Node(ApplyMask(), name="t1w_brain")
    workflow.connect(
        [
            (
                inputnode,
                t1w_brain,
                [("t1w_preproc", "in_file"), ("t1w_mask", "in_mask")],
            ),
            (
                epi_ref_wf,
                brainextraction_wf,
                [("outputnode.dwi_reference_nii", "inputnode.in_file")],
            ),
        ]
    )
    # MAIN WORKFLOW STRUCTURE
    # TODO Make freesurfer's reconall available through this pipeline.
    if config.workflow.run_reconall:
        from niworkflows.anat.coregistration import init_bbreg_wf

        from ...utils.misc import sub_prefix as _prefix

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

        workflow.connect(
            [
                (
                    inputnode,
                    bbr_wf,
                    [
                        ("fsnative2t1w_xfm", "inputnode.fsnative2t1w_xfm"),
                        (("subject_id", _prefix), "inputnode.subject_id"),
                        ("subjects_dir", "inputnode.subjects_dir"),
                    ],
                ),
                # T1w Mask
                (
                    inputnode,
                    t1w_brain,
                    [("t1w_preproc", "in_file"), ("t1w_mask", "in_mask")],
                ),
            ]
            # (inputnode, ds_report_reg, [("dwi_file", "source_file")]),
            # BBRegister
            # (buffernode, bbr_wf, [("dwi_reference", "inputnode.in_file")])]
            #     (bbr_wf, ds_report_reg, [
            #         ("outputnode.out_report", "in_file"),
            #         (("outputnode.fallback", _bold_reg_suffix), "desc")]),
            # ]
        )
    else:
        bbr_wf = init_epireg_wf()
        workflow.connect(
            [
                (t1w_brain, bbr_wf, [("out_file", "inputnode.t1w_brain")]),
                (inputnode, bbr_wf, [("t1w_preproc", "inputnode.t1w_head")]),
            ]
        )

    if "eddy" not in config.workflow.ignore:
        # Eddy distortion correction
        pre_eddy_wf = init_phasediff_wf()
        # workflow.connect([])
        preprocess_wf = init_preprocess_wf()
        ds_report_eddy = pe.Node(
            DerivativesDataSink(
                base_directory=str(config.execution.output_dir),
                desc="eddy",
                datatype="figures",
            ),
            name="ds_report_eddy",
            run_without_submitting=True,
        )

        eddy_report = pe.Node(
            SimpleBeforeAfter(
                before_label="Distorted",
                after_label="Eddy Corrected",
            ),
            name="eddy_report",
            mem_gb=0.1,
        )

        workflow.connect(
            [
                (
                    mif_conversion_wf,
                    pre_eddy_wf,
                    [
                        ("outputnode.dwi_file", "inputnode.dwi_file"),
                        ("outputnode.fmap", "inputnode.fmap"),
                    ],
                ),
                (
                    pre_eddy_wf,
                    preprocess_wf,
                    [
                        (
                            "outputnode.merged_phasediff",
                            "inputnode.merged_phasediff",
                        )
                    ],
                ),
                (
                    mif_conversion_wf,
                    preprocess_wf,
                    [("outputnode.dwi_file", "inputnode.dwi_file")],
                ),
                (
                    preprocess_wf,
                    epi_ref_wf,
                    [("outputnode.dwi_preproc", "inputnode.dwi_file")],
                ),
                (inputnode, ds_report_eddy, [("dwi_file", "source_file")]),
                (
                    pre_eddy_wf,
                    eddy_report,
                    [("outputnode.dwi_reference", "before")],
                ),
                (
                    epi_ref_wf,
                    eddy_report,
                    [("outputnode.dwi_reference_nii", "after")],
                ),
                (eddy_report, ds_report_eddy, [("out_report", "in_file")]),
                (
                    preprocess_wf,
                    apply_transform_wf,
                    [("outputnode.dwi_preproc", "inputnode.dwi_file")],
                ),
                (
                    preprocess_wf,
                    nii_conversion_wf,
                    [
                        (
                            "outputnode.dwi_preproc",
                            "inputnode.native_preproc_dwi",
                        )
                    ],
                ),
                (
                    apply_transform_wf,
                    nii_conversion_wf,
                    [("outputnode.dwi_file", "inputnode.coreg_preproc_dwi")],
                ),
            ]
        )
    else:
        workflow.connect(
            [
                (
                    mif_conversion_wf,
                    epi_ref_wf,
                    [("outputnode.dwi_file", "inputnode.dwi_file")],
                ),
                (
                    mif_conversion_wf,
                    apply_transform_wf,
                    [("outputnode.dwi_file", "inputnode.dwi_file")],
                ),
                (
                    mif_conversion_wf,
                    nii_conversion_wf,
                    [("outputnode.dwi_file", "inputnode.native_preproc_dwi")],
                ),
                (
                    apply_transform_wf,
                    nii_conversion_wf,
                    [("outputnode.dwi_file", "inputnode.coreg_preproc_dwi")],
                ),
            ]
        )
    workflow.connect(
        [
            (
                epi_ref_wf,
                bbr_wf,
                [("outputnode.dwi_reference_nii", "inputnode.in_file")],
            ),
            (
                epi_ref_wf,
                apply_transform_wf,
                [("outputnode.dwi_reference_nii", "inputnode.dwi_reference")],
            ),
            (
                bbr_wf,
                apply_transform_wf,
                [
                    ("outputnode.epi_to_t1w_aff", "inputnode.epi_to_t1w_aff"),
                    ("outputnode.t1w_to_epi_aff", "inputnode.t1w_to_epi_aff"),
                ],
            ),
            (
                t1w_brain,
                apply_transform_wf,
                [("out_file", "inputnode.t1w_brain")],
            ),
            (
                inputnode,
                apply_transform_wf,
                [("t1w_mask", "inputnode.t1w_mask")],
            ),
        ]
    )
    # coreg_epi_ref_wf = init_epi_ref_wf(name="coreg_dwi_reference_wf")
    # coreg_epi_ref_wf.name = "coreg_dwi_reference_wf"
    coreg_epi_ref_wf = epi_ref_wf.clone("coreg_dwi_reference_wf")
    workflow.connect(
        [
            (
                apply_transform_wf,
                coreg_epi_ref_wf,
                [("outputnode.dwi_file", "inputnode.dwi_file")],
            ),
        ]
    )
    ds_preproc_dwi = init_derivatives_wf()
    ds_preproc_dwi.inputs.inputnode.set(
        base_directory=config.execution.output_dir
    )
    workflow.connect(
        [
            (
                inputnode,
                ds_preproc_dwi,
                [("dwi_file", "inputnode.source_file")],
            ),
            (
                nii_conversion_wf,
                ds_preproc_dwi,
                [
                    (
                        "outputnode.native_dwi_file",
                        "inputnode.native_dwi_file",
                    ),
                    (
                        "outputnode.native_dwi_json",
                        "inputnode.native_dwi_json",
                    ),
                    (
                        "outputnode.native_dwi_bvec",
                        "inputnode.native_dwi_bvec",
                    ),
                    (
                        "outputnode.native_dwi_bval",
                        "inputnode.native_dwi_bval",
                    ),
                    (
                        "outputnode.coreg_dwi_file",
                        "inputnode.coreg_dwi_file",
                    ),
                    (
                        "outputnode.coreg_dwi_json",
                        "inputnode.coreg_dwi_json",
                    ),
                    (
                        "outputnode.coreg_dwi_bvec",
                        "inputnode.coreg_dwi_bvec",
                    ),
                    (
                        "outputnode.coreg_dwi_bval",
                        "inputnode.coreg_dwi_bval",
                    ),
                ],
            ),
            (
                epi_ref_wf,
                ds_preproc_dwi,
                [
                    (
                        "outputnode.dwi_reference_nii",
                        "inputnode.native_epi_ref_file",
                    ),
                    (
                        "outputnode.dwi_reference_json",
                        "inputnode.native_epi_ref_json",
                    ),
                ],
            ),
            (
                coreg_epi_ref_wf,
                ds_preproc_dwi,
                [
                    (
                        "outputnode.dwi_reference_nii",
                        "inputnode.coreg_epi_ref_file",
                    ),
                    (
                        "outputnode.dwi_reference_json",
                        "inputnode.coreg_epi_ref_json",
                    ),
                ],
            ),
            (
                bbr_wf,
                ds_preproc_dwi,
                [
                    ("outputnode.epi_to_t1w_aff", "inputnode.epi_to_t1w_aff"),
                    ("outputnode.t1w_to_epi_aff", "inputnode.t1w_to_epi_aff"),
                ],
            ),
            (
                apply_transform_wf,
                ds_preproc_dwi,
                [
                    (
                        "outputnode.native_dwi_mask",
                        "inputnode.native_dwi_mask",
                    ),
                    ("outputnode.coreg_dwi_mask", "inputnode.coreg_dwi_mask"),
                ],
            ),
        ]
    ),
    # (inputnode, ds_report_eddy, [("dwi_file", "source_file")]),
    # (brainextraction_wf, preprocess_wf, [("outputnode.out_mask", "inputnode.dwi_mask")]),
    # (brainextraction_wf, eddy_report, [("outputnode.out_file", "before")]),
    # (eddy_report, ds_report_eddy, [("out_report", "in_file")]),

    # fmt:on
    # return workflow

    # REPORTING ############################################################
    # reportlets_wf = init_reportlets_wf(
    #     str(config.execution.output_dir),
    #     sdc_report=has_fieldmap,
    # )

    # workflow.connect([
    #     (inputnode, reportlets_wf, [("dwi_file", "inputnode.source_file")]),
    #     # (dwi_reference_wf, reportlets_wf, [
    #     #     ("outputnode.validation_report", "inputnode.validation_report"),
    #     # ]),
    #     (outputnode, reportlets_wf, [
    #         ("dwi_reference", "inputnode.dwi_ref"),
    #         ("dwi_mask", "inputnode.dwi_mask"),
    #     ]),
    # ])
    # fmt: on

    # if not has_fieldmap:
    #     workflow.connect([
    #         (brainextraction_wf, buffernode, [
    #             ("outputnode.out_file", "dwi_reference"),
    #             ("outputnode.out_mask", "dwi_mask"),
    #         ]),
    #     ])
    #     # fmt: on
    #     return workflow

    # sdc_report = pe.Node(
    #     SimpleBeforeAfter(
    #         before_label="Distorted",
    #         after_label="Corrected",
    #     ),
    #     name="sdc_report",
    #     mem_gb=0.1,
    # )

    # workflow.connect([
    #     # (brainextraction_wf, sdc_report, [("outputnode.out_file", "before")]),
    #     (sdc_report, reportlets_wf, [("out_report", "inputnode.sdc_report")]),
    # ])
    # fmt: on

    return workflow


def _get_wf_name(filename):
    """
    Derive the workflow name for supplied DWI file.

    Examples
    --------
    >>> _get_wf_name("/completely/made/up/path/sub-01_dir-AP_acq-64grad_dwi.nii.gz")
    'dwi_preproc_dir_AP_acq_64grad_wf'

    >>> _get_wf_name("/completely/made/up/path/sub-01_dir-RL_run-01_echo-1_dwi.nii.gz")
    'dwi_preproc_dir_RL_run_01_echo_1_wf'

    """
    from pathlib import Path

    fname = Path(filename).name.rpartition(".nii")[0].replace("_dwi", "_wf")
    fname_nosub = "_".join(fname.split("_")[1:])
    return f"dwi_preproc_{fname_nosub.replace('.', '_').replace(' ', '').replace('-', '_')}"


def _aslist(value):
    return [value]
