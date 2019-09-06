# -*- coding: utf-8 -*-

"""
SDC using BrainSuite
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_brainsuite_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import brainsuite, utility as niu


def init_brainsuite_wf():

    wf = pe.Workflow(name='brainsuite_wf')

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                'T1w',
                'T1w_mask',
                'dwi_file',
                'dwi_mask',
                'bvec_file',
                'bval_file']),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_dwi']), name='outputnode'
    )

    bias_corr = pe.Node(brainsuite.Bfc(minBias=0.5, maxBias=1.5), name='bias_corr')

    # nipype spec doesn't have an output definition yet!
    bdp = pe.Node(brainsuite.BDP(), name='bdp')

    wf.connect([
        (inputnode, bias_corr, [('T1w', 'inputMRIFile')]),
        (bias_corr, bdp, [('outputMRIVolume', 'bfcFile'),
                          ('T1w_mask', 't1Mask'),
                          ('dwi_file', 'inputDiffusionData'),
                          ('dwi_mask', 'dwiMask'),
                          ('bvec_file', 'BVecBValPair')])
    ])
