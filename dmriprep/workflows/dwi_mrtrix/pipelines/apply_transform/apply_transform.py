from dmriprep.workflows.dwi_mrtrix.pipelines.apply_transform.edges import (
    APPLY_XFM_MASK_TO_OUTPUT_EDGES,
    DWI_XFM_TO_OUTPUT_EDGES,
    INPUT_TO_APPLY_XFM_MASK_EDGES,
    INPUT_TO_DWI_XFM_EDGES,
    INPUT_TO_RESAMPLE_XFM_EDGES,
    INPUT_TO_TRANSFORM_CONVERT_EDGES,
    RESAMPLE_MASK_TO_OUTPUT_EDGES,
    TRANSFORM_CONVERT_TO_DWI_XFM_EDGES,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.apply_transform.nodes import (
    APPLY_XFM_DWI_NODE,
    APPLY_XFM_MASK_NODE,
    INPUT_NODE,
    OUTPUT_NODE,
    RESAMPLE_MASK_NODE,
    TRANSFORM_FSL_AFF_TO_MRTRIX,
)
from nipype.pipeline import engine as pe

APPLY_TRANSFORMS = [
    (
        INPUT_NODE,
        TRANSFORM_FSL_AFF_TO_MRTRIX,
        INPUT_TO_TRANSFORM_CONVERT_EDGES,
    ),
    (INPUT_NODE, APPLY_XFM_DWI_NODE, INPUT_TO_DWI_XFM_EDGES),
    (
        TRANSFORM_FSL_AFF_TO_MRTRIX,
        APPLY_XFM_DWI_NODE,
        TRANSFORM_CONVERT_TO_DWI_XFM_EDGES,
    ),
    (APPLY_XFM_DWI_NODE, OUTPUT_NODE, DWI_XFM_TO_OUTPUT_EDGES),
    (INPUT_NODE, APPLY_XFM_MASK_NODE, INPUT_TO_APPLY_XFM_MASK_EDGES),
    (APPLY_XFM_MASK_NODE, OUTPUT_NODE, APPLY_XFM_MASK_TO_OUTPUT_EDGES),
    (INPUT_NODE, RESAMPLE_MASK_NODE, INPUT_TO_RESAMPLE_XFM_EDGES),
    (RESAMPLE_MASK_NODE, OUTPUT_NODE, RESAMPLE_MASK_TO_OUTPUT_EDGES),
]


def init_apply_transform(name="apply_transform_wf") -> pe.Workflow:
    """
    Initiates a workflow to apply pre-calculated (linear,rigid-body) transform to a list of files.

    Parameters
    ----------
    in_fields : list
        A list of string representing files to apply transform to.
    name : str, optional
        Workflow's name, by default "apply_transform_wf"

    Returns
    -------
    pe.Workflow
        Initiated workflow to apply pre-calculated transform on several files.
    """
    wf = pe.Workflow(name=name)
    wf.connect(APPLY_TRANSFORMS)
    return wf
