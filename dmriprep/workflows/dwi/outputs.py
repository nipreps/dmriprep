# -*- coding: utf-8 -*-

"""
Output dwi
^^^^^^^^^^

.. autofunction:: init_dwi_derivatives_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import io as nio, utility as niu


def init_dwi_derivatives_wf(subject_id, session_id, output_folder):

    output_wf = pe.Workflow(name="output_wf")

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
                "dtifit_MD",
                "dtifit_AD",
                "dtifit_RD",
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
            output_folder, "dmriprep", "sub-" + subject_id, "ses-" + session_id, "dwi"
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

    output_wf.connect(
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
                    ("bvec", "@result.@bvec"),
                    ("bval", "@result.@bval"),
                    ("mask", "@result.@mask"),
                    ("b0", "@result.@b0"),
                    ("eddy_quad_json", "@result.@eddy_quad_json"),
                    ("eddy_quad_pdf", "@result.@eddy_quad_pdf"),
                    ("dtifit_FA", "@result.@fa"),
                    ("dtifit_MD", "@result.@md"),
                    ("dtifit_AD", "@result.@ad"),
                    ("dtifit_RD", "@result.@rd"),
                    ("dtifit_V1", "@result.@v1"),
                    ("dtifit_sse", "@result.@sse"),
                ],
            ),
        ]
    )

    return output_wf
