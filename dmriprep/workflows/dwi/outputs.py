#!/usr/bin/env python


def init_output_wf(subject_id, session_id, output_folder):
    from nipype.pipeline import engine as pe
    from nipype.interfaces import io as nio, utility as niu

    op_wf = pe.Workflow(name="output_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "subject_id",
                "session_id",
                "out_file",
                "out_mask",
                "out_bvec",
                "out_bval",
                "out_b0_brain",
                "out_b0_mask",
                "out_fieldmap_brain",
                "out_eddy_qc",
                "out_FA",
                "out_V1",
                "out_sh_residual",
                "output_folder",
            ]
        ),
        name="inputnode",
    )

    def build_path(output_folder, subject_id, session_id):
        import os.path as op

        return op.join(
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
                    ("out_file", "@result.@dwi"),
                    ("out_bvec", "@result.@bvec"),
                    ("out_bval", "@result.@bval"),
                    ("out_mask", "@result.@mask"),
                    ("out_b0_brain", "@result.@b0brain"),
                    ("out_b0_mask", "@result.@b0mask"),
                    # ("out_fieldmap_brain", "@result.@fmapbrain"),
                    ("out_eddy_qc", "@result.@eddyqc"),
                    ("out_FA", "@result.@fa"),
                    ("out_V1", "@result.@v1"),
                    ("out_sh_residual", "@result.@residual"),
                ],
            ),
        ]
    )

    return op_wf
