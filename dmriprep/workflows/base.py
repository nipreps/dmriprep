#!/usr/bin/env python

import os
from copy import deepcopy

from nipype.pipeline import engine as pe
from .dwi import init_dwi_preproc_wf, init_output_wf


def init_dmriprep_wf(layout, subject_list, work_dir, output_dir):
    dmriprep_wf = pe.Workflow(name="dmriprep_wf")
    dmriprep_wf.base_dir = work_dir

    for subject_id in subject_list:

        single_subject_wf = init_single_subject_wf(
            layout=layout,
            subject_id=subject_id,
            name="single_subject_" + subject_id + "_wf",
            work_dir=work_dir,
            output_dir=output_dir
        )

        single_subject_wf.config["execution"]["crashdump_dir"] = os.path.join(
            output_dir, "dmriprep", "sub-" + subject_id, "log"
        )

        for node in single_subject_wf._get_all_nodes():
            node.config = deepcopy(single_subject_wf.config)

        dmriprep_wf.add_nodes([single_subject_wf])

    return dmriprep_wf


def init_single_subject_wf(layout, subject_id, name, work_dir, output_dir):

    dwi_files = layout.get(
        subject=subject_id,
        datatype="dwi",
        suffix="dwi",
        extensions=[".nii", ".nii.gz"],
        return_type="filename",
    )

    if not dwi_files:
        raise Exception(
            "No dwi images found for participant {}. "
            "All workflows require dwi images".format(subject_id)
        )

    subject_wf = pe.Workflow(name=name)

    for dwi_file in dwi_files:
        entities = layout.parse_file_entities(dwi_file)
        session_id = entities["session"]
        metadata = layout.get_metadata(dwi_file)
        dwi_preproc_wf = init_dwi_preproc_wf(
            subject_id=subject_id, dwi_file=dwi_file, metadata=metadata, layout=layout
        )
        datasink_wf = init_output_wf(
            subject_id=subject_id, session_id=session_id, output_folder=output_dir
        )

        dwi_preproc_wf.base_dir = os.path.join(os.path.abspath(work_dir), subject_id)

        inputspec = dwi_preproc_wf.get_node("inputnode")
        inputspec.inputs.subject_id = subject_id
        inputspec.inputs.dwi_file = dwi_file
        inputspec.inputs.metadata = metadata
        inputspec.inputs.bvec_file = layout.get_bvec(dwi_file)
        inputspec.inputs.bval_file = layout.get_bval(dwi_file)
        inputspec.inputs.out_dir = os.path.abspath(output_dir)

        ds_inputspec = datasink_wf.get_node("inputnode")
        ds_inputspec.inputs.subject_id = subject_id
        ds_inputspec.inputs.session_id = session_id
        ds_inputspec.inputs.output_folder = output_dir
        ds_inputspec.inputs.metadata = metadata

        wf_name = "sub_" + subject_id + "_ses_" + session_id + "_preproc_wf"
        full_wf = pe.Workflow(name=wf_name)

        full_wf.connect(
            [
                (
                    dwi_preproc_wf,
                    datasink_wf,
                    [
                        ("fsl_eddy.out_corrected", "inputnode.out_file"),
                        ("fsl_eddy.out_rotated_bvecs", "inputnode.out_bvec"),
                        ("getB0Mask.mask_file", "inputnode.out_mask"),
                        ("inputnode.bval_file", "inputnode.out_bval"),
                        ("bet_dwi_pre.out_file", "inputnode.out_b0_brain"),
                        ("bet_dwi_pre.mask_file", "inputnode.out_b0_mask"),
                        ("eddy_quad.qc_json", "inputnode.out_eddy_qc"),
                        ("dtifit.FA", "inputnode.out_FA"),
                        ("dtifit.V1", "inputnode.out_V1"),
                        ("denoise_eddy.noise", "inputnode.out_sh_residual"),
                    ],
                )
            ]
        )

        subject_wf.add_nodes([full_wf])

    return subject_wf
