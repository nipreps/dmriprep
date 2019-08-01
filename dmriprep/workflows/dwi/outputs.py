# -*- coding: utf-8 -*-

import os

from nipype.pipeline import engine as pe
from nipype.interfaces import io as nio, utility as niu


def init_output_wf(subject_id, session_id, output_folder):

    op_wf = pe.Workflow(name="output_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "subject_id",
                "session_id",
                "dwi",
                "bval",
                "bvec",
                "index",
                "acq_params",
                "mask",
                "b0",
                "b0_mask",
                "eddy_quad_json",
                "eddy_quad_pdf",
                "dtifit_FA",
                "dtifit_V1",
                "dtifit_sse",
                "noise",
            ]
        ),
        name="inputnode",
    )

    def build_path(output_folder, subject_id, session_id):
        import os

        return os.path.join(
            output_folder,
            "dmriprep",
            "sub-" + subject_id,
            "ses-" + session_id,
            "dwi",
        )

    concat = pe.Node(
        niu.Function(
            input_names=["output_folder", "subject_id", "session_id"],
            output_names=["built_folder"],
            function=build_path,
        ),
        name="build_path",
    )

    datasink = pe.Node(nio.DataSink(), name="datasink")

    op_wf.connect(
        [
            (
                inputnode,
                concat,
                [
                    ("subject_id", "subject_id"),
                    ("session_id", "session_id"),
                    ("output_folder", "output_folder"),
                ],
            ),
            (concat, datasink, [("built_folder", "base_directory")]),
            (
                inputnode,
                datasink,
                [
                    ("dwi", "@result.@dwi"),
                    ("bval", "@result.@bval"),
                    ("bvec", "@result.@bvec"),
                    ("index", "@result.@index"),
                    ("acq_params", "@result.@acq_params"),
                    ("mask", "@result.@mask"),
                    ("b0", "@result.@b0"),
                    ("b0_mask", "@result.@b0_mask"),
                    # ("out_fieldmap_brain", "@result.@fmapbrain"),
                    ("eddy_quad_json", "@result.@eddy_quad_json"),
                    ("eddy_quad_pdf", "@result.@eddy_quad_pdf"),
                    ("dtifit_FA", "@result.@fa"),
                    ("dtifit_V1", "@result.@v1"),
                    ("dtifit_sse", "@result.@sse"),
                    ("noise", "@result.@noise"),
                ],
            ),
        ]
    )

    return op_wf
