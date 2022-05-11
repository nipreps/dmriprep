from dmriprep.workflows.dwi.conversions.nii_to_mif.edges import (
    DWI_CONVERSION_TO_OUTPUT_EDGES,
    FMAP_CONVERSION_TO_OUTPUT_EDGES,
    INPUT_TO_DWI_CONVERSION_EDGES,
    INPUT_TO_FMAP_CONVERSION_EDGES,
    LOCATE_ASSOCIATED_TO_COVERSION_EDGES,
)
from dmriprep.workflows.dwi.conversions.nii_to_mif.nodes import (
    DWI_CONVERSION_NODE,
    FMAP_CONVERSION_NODE,
    INPUT_NODE,
    LOCATE_ASSOCIATED_DWI_NODE,
    LOCATE_ASSOCIATED_FMAP_NODE,
    OUTPUT_NODE,
)

MIF_CONVERSION = [
    (INPUT_NODE, LOCATE_ASSOCIATED_DWI_NODE, INPUT_TO_DWI_CONVERSION_EDGES),
    (INPUT_NODE, LOCATE_ASSOCIATED_FMAP_NODE, INPUT_TO_FMAP_CONVERSION_EDGES),
    (
        LOCATE_ASSOCIATED_DWI_NODE,
        DWI_CONVERSION_NODE,
        LOCATE_ASSOCIATED_TO_COVERSION_EDGES,
    ),
    (
        LOCATE_ASSOCIATED_FMAP_NODE,
        FMAP_CONVERSION_NODE,
        LOCATE_ASSOCIATED_TO_COVERSION_EDGES,
    ),
    (INPUT_NODE, DWI_CONVERSION_NODE, INPUT_TO_DWI_CONVERSION_EDGES),
    (INPUT_NODE, FMAP_CONVERSION_NODE, INPUT_TO_FMAP_CONVERSION_EDGES),
    (DWI_CONVERSION_NODE, OUTPUT_NODE, DWI_CONVERSION_TO_OUTPUT_EDGES),
    (FMAP_CONVERSION_NODE, OUTPUT_NODE, FMAP_CONVERSION_TO_OUTPUT_EDGES),
]

from niworkflows.engine.workflows import LiterateWorkflow as Workflow


def init_nii_to_mif_wf(name="nii_to_mif_wf"):
    """
    Workflow to convert NIfTI files to mif files

    Parameters
    ----------
    name : str, optional
        Name of workflow. Defaults to "nii_to_mif_wf".
    """
    wf = Workflow(name=name)
    wf.connect(MIF_CONVERSION)
    return wf
