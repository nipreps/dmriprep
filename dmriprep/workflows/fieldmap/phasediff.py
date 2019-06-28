#!/usr/bin/env python

def init_phase_wf(layout):
    from nipype.pipeline import engine as pe
    from nipype.interfaces import fsl, utility as niu
    from ...interfaces import Phasediff2Fieldmap, Phases2Fieldmap

    wf = pe.Workflow(name="phase_prep_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["magnitude1", "phasediff", "b0_stripped"]), name="inputnode")

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_fieldmap"]), name="outputnode")

    mag_bet = pe.Node(fsl.BET(frac=0.6, robust=True),
                                    name='mag_bet')

    prep_fmap = pe.Node(fsl.PrepareFieldmap(scanner='SIEMENS'),
                                    name='prep_fmap')

    rad_to_hz = pe.Node(
        fsl.BinaryMaths(operation="div", operand_value=6.28), name="radToHz"
    )

    phases_meta = pe.Node(
        niu.Function(
            input_names=["in_file", "in_layout"], output_names=["out_dict"], function=get_metadata
        ),
        name="phases_meta",
    )
    phases_meta.inputs.in_layout = layout

    phdiff_meta = pe.Node(
        niu.Function(
            input_names=["in_file", "in_layout"], output_names=["out_dict"], function=get_metadata
        ),
        name="phdiff_meta",
    )
    phdiff_meta.inputs.in_layout = layout

    delta_te = pe.Node(
        niu.Function(
            input_names=["in_values"], output_names=["out_value"], function=_delta_te
        ),
        name="delta_te",
    )

    phases2fmap = pe.Node(Phases2Fieldmap(), name='phases2fmap')

    wf.connect(
        [
            # Mag bet
            (inputnode, mag_bet, [("magnitude1", "in_file")]),
            # phases -> phdiff
            (inputnode, phases_meta, [('out_dict', 'in_file')]),
            (phases_meta, phases2fmap, [('out_dict', 'metadatas')]),
            (inputnode, phases2fmap, [('phasediff', 'phase_files')]),
            # phdiff delta_te
            (phases2fmap, phdiff_meta, [('out_file', 'in_file')]),
            (phdiff_meta, delta_te, [('out_dict', 'in_values')]),
            # prep fmap
            (mag_bet, prep_fmap, [("out_file", "in_magnitude")]),
            (phases2fmap, prep_fmap, [('out_file', 'in_phase')]),
            (delta_te, prep_fmap, [('out_value', 'delta_TE')]),
            # radToHz
            (prep_fmap, rad_to_hz, [("out_fieldmap", "in_file")]),
            (rad_to_hz, outputnode, [("out_file", "fieldmap")])
        ]
    )

    return wf


def get_metadata(in_file, in_layout):
    out_dict = in_layout.get_metadata(in_file)
    return out_dict

def _delta_te(in_values, te1=None, te2=None):
    """Read :math:`\Delta_\text{TE}` from BIDS metadata dict"""
    if isinstance(in_values, float):
        te2 = in_values
        te1 = 0.

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
        raise RuntimeError('EchoTime1 and EchoTime2 metadata fields not found. '
                           'Please consult the BIDS specification.')
    if te1 is None:
        raise RuntimeError(
            'EchoTime1 metadata field not found. Please consult the BIDS specification.')
    if te2 is None:
        raise RuntimeError(
            'EchoTime2 metadata field not found. Please consult the BIDS specification.')

    return abs(float(te2) - float(te1))
