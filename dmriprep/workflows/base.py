#!/usr/bin/env python

import os
from copy import deepcopy

from nipype.pipeline import engine as pe
from .dwi import init_dwi_preproc_wf


def init_dmriprep_wf(layout, subject_list, work_dir, output_dir):
    dmriprep_wf = pe.Workflow(name="dmriprep_wf")
    dmriprep_wf.base_dir = work_dir

    for subject_id in subject_list:

        single_subject_wf = init_single_subject_wf(
            layout=layout,
            subject_id=subject_id,
            name="single_subject_" + subject_id + "_wf",
            work_dir=work_dir,
            output_dir=output_dir,
        )

        single_subject_wf.config["execution"]["crashdump_dir"] = os.path.join(
            output_dir, "dmriprep", "sub-" + subject_id, "log"
        )

        for node in single_subject_wf._get_all_nodes():
            node.config = deepcopy(single_subject_wf.config)

        dmriprep_wf.add_nodes([single_subject_wf])

    return dmriprep_wf


def init_single_subject_wf(layout, subject_id, name, work_dir, output_dir):
    from ..utils import collect_data

    subject_data = collect_data(layout, subject_id)[0]

    if not subject_data["dwi"]:
        raise Exception(
            "No dwi images found for participant {}. "
            "All workflows require dwi images".format(subject_id)
        )

    subject_wf = pe.Workflow(name=name)

    for dwi_file in subject_data["dwi"]:
        dwi_preproc_wf = init_dwi_preproc_wf(dwi_file=dwi_file, layout=layout)
        dwi_preproc_wf.base_dir = os.path.join(os.path.abspath(work_dir), subject_id)
        entities = layout.parse_file_entities(dwi_file)
        session_id = entities["session"]

        inputspec = dwi_preproc_wf.get_node("inputnode")
        inputspec.inputs.subject_id = subject_id
        inputspec.inputs.dwi_file = dwi_file
        inputspec.inputs.metadata = layout.get_metadata(dwi_file)
        inputspec.inputs.bvec_file = layout.get_bvec(dwi_file)
        inputspec.inputs.bval_file = layout.get_bval(dwi_file)
        inputspec.inputs.out_dir = os.path.abspath(output_dir)

        subject_wf.add_nodes([dwi_preproc_wf])

    return subject_wf
