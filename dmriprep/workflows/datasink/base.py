#!/usr/bin/env python

def init_output_wf(subject, session, output_folder):
    from nipype.pipeline import engine as pe
    from nipype.interfaces import (freesurfer as fs, fsl, mrtrix3, io as nio, \
                                   utility as niu)
    from nipype import logging

    op_wf = pe.Workflow(name="output_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=[
        'subject',
        'session',
        'out_file',
        'out_mask',
        'out_bvec',
        'output_folder']),
        name="inputnode")

    def build_path(output_folder, subject, session):
        import os.path as op
        return op.join(output_folder, "sub-" + subject, "ses-" + session, "dwi")

    concat = pe.Node(niu.Function(input_names=["output_folder", "subject", "session"], output_names=["built_folder"], function=build_path), name="build_path")

    datasink = pe.Node(nio.DataSink(), name="datasink")

    op_wf.connect(
        [(inputnode, concat, [('subject', 'subject'),
                            ('session', 'session'),
                            ('output_folder', 'output_folder')]),
         (concat, datasink, [('built_folder', 'base_directory')]),
         (inputnode, datasink, [('out_file', '@result.@dwi'),
                             ('out_bvec', '@result.@bvec'),
                             ('out_mask', '@result.@mask')])
         ]
         )


    return op_wf
