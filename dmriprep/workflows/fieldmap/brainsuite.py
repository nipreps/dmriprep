# -*- coding: utf-8 -*-

"""
SDC using BrainSuite
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_brainsuite_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import brainsuite, utility as niu

def init_fmap_wf():

    wf = pe.Workflow(name='brainsuite_wf')

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                'T1w',
                'T1w_mask',
                'dwi_file',
                'dwi_mask']),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_fmap']), name='outputnode'
    )

    bias_corr = pe.Node(brainsuite.Bfc(minBias=0.5, maxBias=1.5), name='bias_corr')

    bdp = pe.Node(brainsuite.BDP(), name='bdp')

    wf.connect([])

# bfc -i $indir2/brain.nii.gz -o T1.bfc.nii.gz

# /KIMEL/tigrlab/quarantine/brainsuite/18a/build/bdp/bdp.sh \
#   T1.bfc.nii.gz \
#   --t1-mask $indir2/brainmaskautobet_mask.nii.gz \
#   --nii $indir1/data.nii.gz \
#   --dwi-mask $indir1/nodif_brain_mask.nii.gz \
#   -b $indir1/bval.txt \
#   -g $indir1/eddy_bvecs.txt
