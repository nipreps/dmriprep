#!/usr/bin/env python

from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, ants, utility as niu
from ...interfaces import Phases2Fieldmap


def init_phase_wf(bet_mag):

    wf = pe.Workflow(name='phase_prep_wf')

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['magnitude1', 'phasediff', 'b0_stripped', 'phases_meta']),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_fmap', 'out_mag']),
        name='outputnode')

    phases2fmap = pe.Node(Phases2Fieldmap(), name='phases2fmap')

    phdiff_wf = init_phdiff_wf(bet_mag)

    wf.connect([
        (inputnode, phases2fmap, [('phases_meta', 'metadatas')]),
        (inputnode, phases2fmap, [('phasediff', 'phase_files')]),
        (inputnode, phdiff_wf, [('magnitude1', 'inputnode.magnitude1'),
                                ('phases_meta', 'inputnode.phases_meta')]),
        (phases2fmap, phdiff_wf, [('out_file', 'inputnode.phasediff')])
        (phdiff_wf, outputnode, [('outputnode.out_fmap', 'out_fmap'),
                                 ('outputnode.out_mag', 'out_mag')])
    ])

    return wf


def init_phdiff_wf(bet_mag):

    wf = pe.Workflow(name='phdiff_prep_wf')

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['magnitude1', 'phasediff', 'phases_meta']),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_fmap', 'out_mag']),
        name='outputnode')

    n4_correct = pe.Node(
        ants.N4BiasFieldCorrection(dimension=3, copy_header=True),
        name='n4_correct')

    mag_bet = pe.Node(
        fsl.BET(frac=bet_mag, robust=True, mask=True), name='mag_bet')

    prep_fmap = pe.Node(
        fsl.PrepareFieldmap(scanner='SIEMENS'), name='prep_fmap')

    fslroi = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name='fslroi_phase')

    delta = pe.Node(
        niu.Function(
            input_names=['in_values'],
            output_names=['out_value'],
            function=delta_te),
        name='delta')

    wf.connect([
        (inputnode, n4_correct, [('magnitude1', 'input_image')]),
        (n4_correct, mag_bet, [('output_image', 'in_file')]),
        (inputnode, delta, [('phases_meta', 'in_values')]),
        (mag_bet, prep_fmap, [('out_file', 'in_magnitude')]),
        (inputnode, prep_fmap, [('phasediff', 'in_phase')]),
        (delta, prep_fmap, [('out_value', 'delta_TE')]),
        (prep_fmap, fslroi, [('out_fieldmap', 'in_file')]),
        (fslroi, outputnode, [('roi_file', 'out_fmap')]),
        (mag_bet, outputnode, [('out_file', 'out_mag')])
    ])

    return wf


def delta_te(in_values, te1=None, te2=None):
    """
    Read :math:`\Delta_\text{TE}` from BIDS metadata dict
    """
    if isinstance(in_values, float):
        te2 = in_values
        te1 = 0.0

    if isinstance(in_values, dict):
        te1 = in_values.get('EchoTime1')
        te2 = in_values.get('EchoTime2')

        if not all((te1, te2)):
            te2 = in_values.get('EchoTimeDifference')
            te1 = 0

    if isinstance(in_values, list):
        te2, te1 = in_values
        if isinstance(te1, list):
            te1 = te1[1]
        if isinstance(te2, list):
            te2 = te2[1]

    # For convienience if both are missing we should give one error about them
    if te1 is None and te2 is None:
        raise RuntimeError(
            'EchoTime1 and EchoTime2 metadata fields not found. '
            'Please consult the BIDS specification.'
        )
    if te1 is None:
        raise RuntimeError(
            'EchoTime1 metadata field not found. Please consult the BIDS specification.'
        )
    if te2 is None:
        raise RuntimeError(
            'EchoTime2 metadata field not found. Please consult the BIDS specification.'
        )

    return 1000 * abs(float(te2) - float(te1))
