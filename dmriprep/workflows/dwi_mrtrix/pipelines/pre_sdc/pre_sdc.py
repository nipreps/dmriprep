import nipype.pipeline.engine as pe
from dmriprep.workflows.dwi_mrtrix.pipelines.pre_sdc.edges import (
    DWIEXTRACT_TO_MRMATH_EDGES,
    INPUT_TO_DWIEXTRACT_EDGES,
    INPUT_TO_MERGE_EDGES,
    MERGE_TO_MRCAT_EDGES,
    MRCAT_TO_OUTPUT_EDGES,
    MRMATH_TO_MERGE_EDGES,
    MRMATH_TO_OUTPUT_EDGES,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.pre_sdc.nodes import (
    DWIEXTRACT_NODE,
    INPUT_NODE,
    MERGE_NODE,
    MRCAT_NODE,
    MRMATH_NODE,
    OUTPUT_NODE,
)

PHASEDIFF = [
    (INPUT_NODE, MERGE_NODE, INPUT_TO_MERGE_EDGES),
    (INPUT_NODE, DWIEXTRACT_NODE, INPUT_TO_DWIEXTRACT_EDGES),
    (DWIEXTRACT_NODE, MRMATH_NODE, DWIEXTRACT_TO_MRMATH_EDGES),
    (MRMATH_NODE, MERGE_NODE, MRMATH_TO_MERGE_EDGES),
    (MERGE_NODE, MRCAT_NODE, MERGE_TO_MRCAT_EDGES),
    (MRCAT_NODE, OUTPUT_NODE, MRCAT_TO_OUTPUT_EDGES),
    (MRMATH_NODE, OUTPUT_NODE, MRMATH_TO_OUTPUT_EDGES),
]


def init_phasediff_wf(name="phasediff_prep_wf") -> pe.Workflow:
    """
    Initiates the preperation for SDC workflow.

    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "phasediff_prep_wf"

    Returns
    -------
    pe.Workflow
        Initiated workflow for phasediff preperation for SDC.
    """
    wf = pe.Workflow(name=name)
    wf.connect(PHASEDIFF)
    return wf


def add_fieldmaps_to_wf(
    inputnode: pe.Node,
    conversion_wf: pe.Workflow,
    epi_ref_wf: pe.Workflow,
    phasediff_wf: pe.Workflow,
) -> list:
    """
    Adds the correct combination of SBRef/mean B0 images for SDC to the main workflow.

    Parameters
    ----------
    inputnode : pe.Node
        Main workflow's input node.
    conversion_wf : pe.Workflow
        Conversion-to-mif node.
    epi_ref_wf : pe.Workflow
        EPI reference node (Mean B0)
    phasediff_wf : pe.Workflow
        Phasediff preperation workflow

    Returns
    -------
    list
        List of tuples describing correct edges available within the dataset for SDC.

    Raises
    ------
    NotImplementedError
        [description]
    """

    fmap_ap, fmap_pa = [
        getattr(inputnode.inputs, key, None) for key in ["fmap_ap", "fmap_pa"]
    ]
    if fmap_ap and fmap_pa:
        connection = [
            (
                conversion_wf,
                phasediff_wf,
                [
                    ("outputnode.fmap_ap", "inputnode.fmap_ap"),
                    ("outputnode.fmap_pa", "inputnode.fmap_pa"),
                ],
            )
        ]

    else:
        if fmap_pa is not None:
            connection = [
                (
                    epi_ref_wf,
                    phasediff_wf,
                    [
                        ("outputnode.epi_ref_file", "inputnode.fmap_ap"),
                    ],
                ),
                (
                    conversion_wf,
                    phasediff_wf,
                    [("outputnode.fmap_pa", "inputnode.fmap_pa")],
                ),
            ]

        elif fmap_ap is not None:
            connection = [
                (
                    epi_ref_wf,
                    phasediff_wf,
                    [
                        ("outputnode.epi_ref_file", "inputnode.fmap_pa"),
                    ],
                ),
                (
                    conversion_wf,
                    phasediff_wf,
                    [("outputnode.fmap_ap", "inputnode.fmap_ap")],
                ),
            ]
        else:
            raise NotImplementedError(
                "Currently fieldmap-based SDC is mandatory and thus requires at least one opposite single-volume EPI image."
            )
    return connection
