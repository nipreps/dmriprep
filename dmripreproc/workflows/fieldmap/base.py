#!/usr/bin/env python

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu

FMAP_PRIORITY = {"epi": 0, "fieldmap": 1, "phasediff": 2, "phase": 3, "syn": 4}


def init_sdc_prep_wf(
    subject_id,
    fmaps,
    metadata,
    layout,
    bet_mag_frac,
    synb0,
    omp_nthreads=1,
    fmap_bspline=False,
):

    sdc_prep_wf = pe.Workflow(name="sdc_prep_wf")

    inputnode = pe.Node(
        niu.IdentityInterface(fields=["b0_stripped"]), name="inputnode"
    )

    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "out_fmap",
                "out_topup",
                "bold_ref",
                "bold_mask",
                "bold_ref_brain",
                "out_warp",
                "syn_bold_ref",
                "method",
                "out_movpar",
                "out_enc_file",
            ]
        ),
        name="outputnode",
    )
    if (synb0):
        from .pepolar import init_synb0_wf

        synb0_wf = init_synb0_wf(subject_id, metadata, synb0)

        sdc_prep_wf.connect(
            [
                (
                    inputnode,
                    synb0_wf,
                    [("b0_stripped", "inputnode.b0_stripped")],
                ),
                (
                    synb0_wf,
                    outputnode,
                    [
                        ("outputnode.out_topup", "out_topup"),
                        ("outputnode.out_movpar", "out_movpar"),
                        ("outputnode.out_enc_file", "out_enc_file"),
                        ("outputnode.out_fmap", "out_fmap")
                    ],
                )
            ]
        )
    else:
        fmaps.sort(key=lambda fmap: FMAP_PRIORITY[fmap["suffix"]])
        fmap = fmaps[0]

        if fmap["suffix"] == "epi":
            from .pepolar import init_pepolar_wf

            epi_fmaps = [
                (fmap_["epi"], fmap_["metadata"]["PhaseEncodingDirection"])
                for fmap_ in fmaps
                if fmap_["suffix"] == "epi"
            ]

            pepolar_wf = init_pepolar_wf(subject_id, metadata, epi_fmaps)

            sdc_prep_wf.connect(
                [
                    (
                        inputnode,
                        pepolar_wf,
                        [("b0_stripped", "inputnode.b0_stripped")],
                    ),
                    (
                        pepolar_wf,
                        outputnode,
                        [
                            ("outputnode.out_topup", "out_topup"),
                            ("outputnode.out_movpar", "out_movpar"),
                            ("outputnode.out_enc_file", "out_enc_file"),
                            ("outputnode.out_fmap", "out_fmap")
                        ],
                    )
                ]
            )

        if fmap["suffix"] == "fieldmap":
            from .fmap import init_fmap_wf

            fmap_wf = init_fmap_wf()
            fmap_wf.inputs.inputnode.fieldmap = fmap["fieldmap"]
            fmap_wf.inputs.inputnode.magnitude = fmap["magnitude"]

            sdc_prep_wf.connect(
                [
                    (
                        inputnode,
                        fmap_wf,
                        [("b0_stripped", "inputnode.b0_stripped")],
                    ),
                    (fmap_wf, outputnode, [("outputnode.out_fmap", "out_fmap")]),
                ]
            )

        if fmap["suffix"] in ("phasediff", "phase"):
            from .phasediff import init_phase_wf, init_phdiff_wf
            from .fmap import init_fmap_wf

            if fmap["suffix"] == "phasediff":
                phase_wf = init_phdiff_wf(bet_mag_frac)
                phase_wf.inputs.inputnode.phasediff = fmap["phasediff"]

                phase_wf.inputs.inputnode.magnitude1 = [
                    fmap_
                    for key, fmap_ in sorted(fmap.items())
                    if key.startswith("magnitude1")
                ][0]

                phase_wf.inputs.inputnode.phases_meta = layout.get_metadata(
                    phase_wf.inputs.inputnode.phasediff
                )
                post_phase_wf = init_fmap_wf()

                sdc_prep_wf.connect(
                    [
                        (
                            inputnode,
                            post_phase_wf,
                            [("b0_stripped", "inputnode.b0_stripped")],
                        ),
                        (
                            phase_wf,
                            post_phase_wf,
                            [("outputnode.out_fmap", "inputnode.fieldmap")],
                        ),
                        (
                            phase_wf,
                            post_phase_wf,
                            [("outputnode.out_mag", "inputnode.magnitude")],
                        ),
                        (
                            post_phase_wf,
                            outputnode,
                            [("outputnode.out_fmap", "out_fmap")],
                        ),
                    ]
                )

            elif fmap["suffix"] == "phase":
                phase_wf = init_phase_wf(bet_mag_frac)
                phase_wf.inputs.inputnode.phasediff = [
                    fmap["phase1"],
                    fmap["phase2"],
                ]

                phase_wf.inputs.inputnode.magnitude1 = [
                    fmap_
                    for key, fmap_ in sorted(fmap.items())
                    if key.startswith("magnitude1")
                ][0]

                phase_wf.inputs.inputnode.phases_meta = [
                    layout.get_metadata(i)
                    for i in phase_wf.inputs.inputnode.phasediff
                ]
                post_phase_wf = init_fmap_wf()

                sdc_prep_wf.connect(
                    [
                        (
                            inputnode,
                            post_phase_wf,
                            [("b0_stripped", "inputnode.b0_stripped")],
                        ),
                        (
                            phase_wf,
                            post_phase_wf,
                            [("outputnode.out_fmap", "inputnode.fieldmap")],
                        ),
                        (
                            phase_wf,
                            post_phase_wf,
                            [("outputnode.out_mag", "inputnode.magnitude")],
                        ),
                        (
                            post_phase_wf,
                            outputnode,
                            [("outputnode.out_fmap", "out_fmap")],
                        ),
                    ]
                )
    return sdc_prep_wf
