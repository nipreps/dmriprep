#!/usr/bin/env python

FMAP_PRIORITY = {"epi": 0, "fieldmap": 1, "phasediff": 2, "phase": 3, "syn": 4}


def init_sdc_prep_wf(fmaps, dwi_meta, layout, omp_nthreads=1, fmap_bspline=False):
    from nipype.pipeline import engine as pe
    from nipype.interfaces import utility as niu

    sdc_prep_wf = pe.Workflow(name="sdc_prep_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["b0_stripped"]), name="inputnode")

    #outputnode = pe.Node(niu.IdentityInterface(fields=["out_fmap",]), name="outputnode")

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "out_fmap",
                "bold_ref",
                "bold_mask",
                "bold_ref_brain",
                "out_warp",
                "syn_bold_ref",
                "method"
            ]
        ),
        name="outputnode",
    )

    fmaps.sort(key=lambda fmap: FMAP_PRIORITY[fmap["suffix"]])
    fmap = fmaps[0]

    if fmap["suffix"] == "fieldmap":
        from .fmap import init_fmap_wf

        fmap_wf = init_fmap_wf()
        fmap_wf.inputs.inputnode.fieldmap = fmap["fieldmap"]
        fmap_wf.inputs.inputnode.magnitude = fmap["magnitude"]

        sdc_prep_wf.connect(
            [
                (inputnode, fmap_wf, [("b0_stripped", "inputnode.b0_stripped")]),
                (fmap_wf, outputnode, [("outputnode.out_fmap", "out_fmap")]),
            ]
        )

    if fmap['suffix'] in ('phasediff', 'phase'):
        from .phdiff import init_phdiff_wf
        fmap_estimator_wf = init_phdiff_wf(omp_nthreads=omp_nthreads,
                                            phasetype=fmap['suffix'],
                                            layout=layout)
        if fmap['suffix'] == 'phasediff':
            fmap_estimator_wf.inputs.inputnode.phasediff = fmap['phasediff']
        elif fmap['suffix'] == 'phase':
            # Check that fieldmap is not bipolar
            fmap_polarity = fmap['metadata'].get('DiffusionScheme', None)
            if fmap_polarity == 'Bipolar':
                LOGGER.warning("Bipolar fieldmaps are not supported. Ignoring")
                sdc_prep_wf.__postdesc__ = ""
                outputnode.inputs.method = 'None'
                sdc_prep_wf.connect([
                    (inputnode, outputnode, [('bold_ref', 'bold_ref'),
                                             ('bold_mask', 'bold_mask'),
                                             ('bold_ref_brain', 'bold_ref_brain')]),
                ])
                return sdc_prep_wf
            if fmap_polarity is None:
                LOGGER.warning("Assuming phase images are Monopolar")

            fmap_estimator_wf.inputs.inputnode.phasediff = [fmap['phase1'], fmap['phase2']]

        fmap_estimator_wf.inputs.inputnode.magnitude = [
            fmap_ for key, fmap_ in sorted(fmap.items())
            if key.startswith("magnitude")
        ]

        sdc_unwarp_wf = init_sdc_unwarp_wf(
            omp_nthreads=omp_nthreads,
            fmap_demean=fmap_demean,
            debug=debug,
            name='sdc_unwarp_wf')
        sdc_unwarp_wf.inputs.inputnode.metadata = bold_meta

        sdc_prep_wf.connect([
            (inputnode, sdc_unwarp_wf, [
                ('bold_ref', 'inputnode.in_reference'),
                ('bold_ref_brain', 'inputnode.in_reference_brain'),
                ('bold_mask', 'inputnode.in_mask')]),
            (fmap_estimator_wf, sdc_unwarp_wf, [
                ('outputnode.fmap', 'inputnode.fmap'),
                ('outputnode.fmap_ref', 'inputnode.fmap_ref'),
                ('outputnode.fmap_mask', 'inputnode.fmap_mask')]),
        ])

        sdc_prep_wf.connect([
            (sdc_unwarp_wf, outputnode, [
                ('outputnode.out_warp', 'out_warp'),
                ('outputnode.out_reference', 'bold_ref'),
                ('outputnode.out_reference_brain', 'bold_ref_brain'),
                ('outputnode.out_mask', 'bold_mask')]),
        ])
    return sdc_prep_wf
