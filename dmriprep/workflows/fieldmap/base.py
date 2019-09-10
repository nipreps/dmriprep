#!/usr/bin/env python

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype import logging

from niworkflows.engine.workflows import LiterateWorkflow as Workflow

LOGGER = logging.getLogger('nipype.workflow')
FMAP_PRIORITY = {
    'epi': 0,
    'fieldmap': 1,
    'phasediff': 2,
    'phase': 3,
    'syn': 4
}


def init_sdc_wf(
    subject_id,
    fmaps,
    metadata,
    layout,
    ignore
):

    sdc_wf = Workflow(name='sdc_wf')

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['dwi_ref', 'dwi_ref_brain', 'dwi_mask',
                't1_brain', 'std2anat_xfm', 'template', 'templates']),
        name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['dwi_ref', 'dwi_ref_brain', 'dwi_mask',
                'out_fmap', 'out_topup', 'out_movpar', 'out_enc_file',
                'out_warp', 'syn_dwi_ref', 'method']),
        name='outputnode')

    fmaps.sort(key=lambda fmap: FMAP_PRIORITY[fmap['suffix']])

    # No fieldmaps
    if not fmaps or 'fieldmaps' in ignore:
        sdc_wf.__postdesc__ = """\
Susceptibility distortion correction (SDC) has been skipped because the
dataset does not contain extra field map acquisitions correctly described
with metadata, and the experimental SDC-SyN method was not explicitly selected.
"""

    outputnode.inputs.method = 'None'
    sdc_wf.connect([
        (inputnode, outputnode, [('dwi_ref', 'dwi_ref'),
                                 ('dwi_ref_brain', 'dwi_ref_brain'),
                                 ('dwi_mask', 'dwi_mask')])
    ])
    return sdc_wf

    sdc_wf.__postdesc__ = """\
Creating fieldmap
"""

    fmap = fmaps[0]

    # topup
    if fmap['suffix'] == 'epi':
        from .pepolar import init_pepolar_wf
        outputnode.inputs.method = 'topup'

        epi_fmaps = [
            (fmap_['epi'], fmap_['metadata']['PhaseEncodingDirection'])
            for fmap_ in fmaps
            if fmap_['suffix'] == 'epi'
        ]

        pepolar_wf = init_pepolar_wf(subject_id, metadata, epi_fmaps)

        sdc_wf.connect([
            (inputnode, pepolar_wf, [('dwi_ref_brain', 'inputnode.b0_stripped')]),
            (pepolar_wf, outputnode, [('outputnode.out_topup', 'out_topup'),
                                      ('outputnode.out_movpar', 'out_movpar'),
                                      ('outputnode.out_enc_file', 'out_enc_file'),
                                      ('outputnode.out_fmap', 'out_fmap')])
        ])

    # fieldmap
    elif fmap['suffix'] == 'fieldmap':
        from .fmap import init_fmap_wf

        fmap_wf = init_fmap_wf()
        fmap_wf.inputs.inputnode.fieldmap = fmap['fieldmap']
        fmap_wf.inputs.inputnode.magnitude = fmap['magnitude']

        sdc_wf.connect([
            (inputnode, fmap_wf, [('b0_stripped', 'inputnode.b0_stripped')]),
            (fmap_wf, outputnode, [('outputnode.out_fmap', 'out_fmap')])
        ])

    elif fmap['suffix'] in ('phasediff', 'phase'):
        from .phasediff import init_phase_wf, init_phdiff_wf
        from .fmap import init_fmap_wf

        if fmap['suffix'] == 'phasediff':
            phase_wf = init_phdiff_wf()
            phase_wf.inputs.inputnode.phasediff = fmap['phasediff']
            phase_wf.inputs.inputnode.magnitude1 = [
                fmap_
                for key, fmap_ in sorted(fmap.items())
                if key.startswith('magnitude1')
            ][0]
            phase_wf.inputs.inputnode.phases_meta = layout.get_metadata(
                phase_wf.inputs.inputnode.phasediff)

            fmap_wf = init_fmap_wf()

            sdc_wf.connect([
                (inputnode, fmap_wf, [('b0_stripped', 'inputnode.b0_stripped')]),
                (phase_wf, fmap_wf, [('outputnode.out_fmap', 'inputnode.fieldmap')]),
                (phase_wf, fmap_wf, [('outputnode.out_mag', 'inputnode.magnitude')]),
                (fmap_wf, outputnode, [('outputnode.out_fmap', 'out_fmap')])
            ])

        elif fmap['suffix'] == 'phase':
            phase_wf = init_phase_wf()
            phase_wf.inputs.inputnode.phasediff = [
                fmap['phase1'],
                fmap['phase2']
            ]
            phase_wf.inputs.inputnode.magnitude1 = [
                fmap_
                for key, fmap_ in sorted(fmap.items())
                if key.startswith('magnitude1')
            ][0]
            phase_wf.inputs.inputnode.phases_meta = [
                layout.get_metadata(i)
                for i in phase_wf.inputs.inputnode.phasediff
            ]

            fmap_wf = init_fmap_wf()

            sdc_wf.connect([
                (inputnode, fmap_wf, [('b0_stripped', 'inputnode.b0_stripped')]),
                (phase_wf, fmap_wf, [('outputnode.out_fmap', 'inputnode.fieldmap')]),
                (phase_wf, fmap_wf, [('outputnode.out_mag', 'inputnode.magnitude')]),
                (fmap_wf, outputnode, [('outputnode.out_fmap', 'out_fmap')])
            ])
    else:
        print('No sdc correction')
    return sdc_wf
