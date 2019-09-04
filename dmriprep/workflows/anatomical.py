# -*- coding: utf-8 -*-

"""
Orchestrating the T1w preprocessing workflows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_anat_preproc_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu

from niworkflows.anat.ants import init_brain_extraction_wf


def init_anat_preproc_wf()
    """
    """

    wf = pe.Workflow(name='init_anat_preproc_wf')

    inputnode = pe.Node(niu.IdentityInterface(fields=['T1w_file']), name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file']), name='outputnode')

    t1_skullstrip = init_brain_extraction_wf()

    to_list = lambda x: [x]

    wf.connect([
        (inputnode, t1_skullstrip, [(('t1_file', to_list), 'inputnode.in_files')]),
        (t1_skullstrip, outputnode, [('outputnode.out_file', 'out_file')])
    ])

    return wf
