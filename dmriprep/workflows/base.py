#!/usr/bin/env python

"""
dMRIprep base processing workflows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_dmriprep_wf
.. autofunction:: init_single_subject_wf

"""

import os
from copy import deepcopy

from nipype.pipeline import engine as pe
from .dwi import init_dwi_preproc_wf, init_output_wf


def init_dmriprep_wf(parameters):
    """
    This workflow organizes the execusion of dMRIPrep, with a sub-workflow for
    each subject.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

    wf = init_dmriprep_wf()

    Parameters

    """
    dmriprep_wf = pe.Workflow(name="dmriprep_wf")
    dmriprep_wf.base_dir = parameters.work_dir

    for subject_id in parameters.subject_list:

        single_subject_wf = init_single_subject_wf(
            subject_id=subject_id,
            name="single_subject_" + subject_id + "_wf",
            parameters=parameters
        )

        single_subject_wf.config["execution"]["crashdump_dir"] = os.path.join(
            parameters.output_dir, "dmriprep", "sub-" + subject_id, "log"
        )
        single_subject_wf.config["execution"]["remove_unnecessary_outputs"] = False
        single_subject_wf.config["execution"]["keep_inputs"] = True
        single_subject_wf.config["execution"]["crashfile_format"] = "txt"

        for node in single_subject_wf._get_all_nodes():
            node.config = deepcopy(single_subject_wf.config)

        dmriprep_wf.add_nodes([single_subject_wf])

    return dmriprep_wf


def init_single_subject_wf(subject_id, name, parameters):
    """
    This workflow organizes the preprocessing pipeline for a single subject.
    It collects and reports information about the subject, and prepares
    sub-workflows to perform diffusion preprocessing.

    Diffusion preprocessing is performed using a separate workflow for each
    individual dwi series.

    .. workflow::
        :graph2use: orig
        :simple_form: yes

    wf = init_single_subject_wf()

    Parameters

    Inputs

    """

    dwi_files = parameters.layout.get(
        subject=subject_id,
        datatype="dwi",
        suffix="dwi",
        extensions=[".nii", ".nii.gz"],
        return_type="filename"
    )

    if not dwi_files:
        raise Exception(
            "No dwi images found for participant {}. "
            "All workflows require dwi images".format(subject_id)
        )

    subject_wf = pe.Workflow(name=name)

    for dwi_file in dwi_files:
        entities = parameters.layout.parse_file_entities(dwi_file)
        if "session" in entities:
            session_id = entities["session"]
        else:
            session_id = None
        metadata = parameters.layout.get_metadata(dwi_file)
        dwi_preproc_wf = init_dwi_preproc_wf(
            subject_id=subject_id,
            dwi_file=dwi_file,
            metadata=metadata,
            parameters=parameters
        )
        datasink_wf = init_output_wf(
            subject_id=subject_id,
            session_id=session_id,
            output_folder=parameters.output_dir
        )

        dwi_preproc_wf.base_dir = os.path.join(
            os.path.abspath(parameters.work_dir), subject_id
        )

        inputspec = dwi_preproc_wf.get_node("inputnode")
        inputspec.inputs.subject_id = subject_id
        inputspec.inputs.dwi_file = dwi_file
        inputspec.inputs.dwi_meta = metadata
        inputspec.inputs.bvec_file = parameters.layout.get_bvec(dwi_file)
        inputspec.inputs.bval_file = parameters.layout.get_bval(dwi_file)
        inputspec.inputs.out_dir = os.path.abspath(parameters.output_dir)

        ds_inputspec = datasink_wf.get_node("inputnode")
        ds_inputspec.inputs.subject_id = subject_id
        ds_inputspec.inputs.session_id = session_id
        ds_inputspec.inputs.output_folder = parameters.output_dir
        ds_inputspec.inputs.metadata = metadata

        if session_id:
            wf_name = "sub_" + subject_id + "_ses_" + session_id + "_preproc_wf"
        else:
            wf_name = "sub_" + subject_id + "_preproc_wf"
        full_wf = pe.Workflow(name=wf_name)

        full_wf.connect(
            [
                (
                    dwi_preproc_wf,
                    datasink_wf,
                    [
                        ("outputnode.out_dwi", "inputnode.dwi"),
                        ("outputnode.out_bval", "inputnode.bval"),
                        ("outputnode.out_bvec", "inputnode.bvec"),
                        ("outputnode.index", "inputnode.index"),
                        ("outputnode.acq_params", "inputnode.acq_params"),
                        ("outputnode.out_mask", "inputnode.mask"),
                        ("outputnode.out_b0_pre", "inputnode.b0"),
                        ("outputnode.out_b0_mask_pre", "inputnode.b0_mask"),
                        ("outputnode.out_eddy_quad_json", "inputnode.eddy_quad_json"),
                        ("outputnode.out_eddy_quad_pdf", "inputnode.eddy_quad_pdf"),
                        ("outputnode.out_dtifit_FA", "inputnode.dtifit_FA"),
                        ("outputnode.out_dtifit_V1", "inputnode.dtifit_V1"),
                        ("outputnode.out_dtifit_sse", "inputnode.dtifit_sse"),
                        ("outputnode.out_noise", "inputnode.noise")
                    ]
                )
            ]
        )

        subject_wf.add_nodes([full_wf])

    return subject_wf
