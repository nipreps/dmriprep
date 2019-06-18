#!/usr/bin/env python

FMAP_PRIORITY = {"epi": 0, "fieldmap": 1, "phasediff": 2, "phase": 3, "syn": 4}


def init_sdc_prep_wf(fmaps, dwi_meta):
    from nipype.pipeline import engine as pe
    from nipype.interfaces import utility as niu

    sdc_prep_wf = pe.Workflow(name="sdc_prep_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["b0_stripped"]), name="inputnode")

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_fmap"]), name="outputnode")

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

    return sdc_prep_wf
