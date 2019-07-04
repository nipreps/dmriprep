#!/usr/bin/env python

FMAP_PRIORITY = {"epi": 0, "fieldmap": 1, "phasediff": 2, "phase": 3, "syn": 4}


def init_sdc_prep_wf(fmaps, metadata, layout, omp_nthreads=1, fmap_bspline=False):
    from nipype.pipeline import engine as pe
    from nipype.interfaces import utility as niu

    sdc_prep_wf = pe.Workflow(name="sdc_prep_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["b0_stripped"]), name="inputnode")

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
        from .phasediff import init_phase_wf, init_phdiff_wf
        from .fmap import init_fmap_wf
        if fmap['suffix'] == 'phasediff':
            phase_wf = init_phdiff_wf()
            phase_wf.inputs.inputnode.phasediff = fmap['phasediff']

            phase_wf.inputs.inputnode.magnitude1 = [
                fmap_ for key, fmap_ in sorted(fmap.items())
                if key.startswith("magnitude1")
            ][0]

            phase_wf.inputs.inputnode.phases_meta = layout.get_metadata(phase_wf.inputs.inputnode.phasediff)
            post_phase_wf = init_fmap_wf()

            sdc_prep_wf.connect(
                [
                    (inputnode, post_phase_wf, [("b0_stripped", "inputnode.b0_stripped")]),
                    (phase_wf, post_phase_wf, [("outputnode.out_fmap", "inputnode.fieldmap")]),
                    (phase_wf, post_phase_wf, [("outputnode.out_mag", "inputnode.magnitude")]),
                    (post_phase_wf, outputnode, [("outputnode.out_fmap", "out_fmap")])
                ]
            )

        elif fmap['suffix'] == 'phase':
            phase_wf = init_phase_wf()
            phase_wf.inputs.inputnode.phasediff = [fmap['phase1'], fmap['phase2']]

            phase_wf.inputs.inputnode.magnitude1 = [
                fmap_ for key, fmap_ in sorted(fmap.items())
                if key.startswith("magnitude1")
            ][0]

            phase_wf.inputs.inputnode.phases_meta = [
                layout.get_metadata(i)
                for i in phase_wf.inputs.inputnode.phasediff
            ]
            post_phase_wf = init_fmap_wf()

            sdc_prep_wf.connect(
                [
                    (inputnode, post_phase_wf, [("b0_stripped", "inputnode.b0_stripped")]),
                    (phase_wf, post_phase_wf, [("outputnode.out_fmap", "inputnode.fieldmap")]),
                    (phase_wf, post_phase_wf, [("outputnode.out_mag", "inputnode.magnitude")]),
                    (post_phase_wf, outputnode, [("outputnode.out_fmap", "out_fmap")])
                ]
            )
    return sdc_prep_wf
