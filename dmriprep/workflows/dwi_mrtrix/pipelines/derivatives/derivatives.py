import nipype.pipeline.engine as pe
from dmriprep.workflows.dwi_mrtrix.pipelines.derivatives.edges import (
    COREG_DWI_LIST_TO_DDS_EDGES,
    COREG_SBREF_LIST_TO_DDS_EDGES,
    INPUT_TO_COREG_DWI_DDS_EDGES,
    INPUT_TO_COREG_DWI_LIST_EDGES,
    INPUT_TO_COREG_DWI_MASK_EDGES,
    INPUT_TO_COREG_SBREF_DDS_EDGES,
    INPUT_TO_COREG_SBREF_LIST_EDGES,
    INPUT_TO_EPI_TO_T1_EDGES,
    INPUT_TO_NATIVE_DWI_DDS_EDGES,
    INPUT_TO_NATIVE_DWI_LIST_EDGES,
    INPUT_TO_NATIVE_DWI_MASK_EDGES,
    INPUT_TO_NATIVE_SBREF_DDS_EDGES,
    INPUT_TO_NATIVE_SBREF_LIST_EDGES,
    INPUT_TO_T1_TO_EPI_EDGES,
    NATIVE_DWI_LIST_TO_DDS_EDGES,
    NATIVE_SBREF_LIST_TO_DDS_EDGES,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.derivatives.nodes import (
    COREG_DWI_DDS_NODE,
    COREG_DWI_LIST_NODE,
    COREG_DWI_MASK_NODE,
    COREG_SBREF_DDS_NODE,
    COREG_SBREF_LIST_NODE,
    EPI_TO_T1_NODE,
    INPUT_NODE,
    NATIVE_DWI_DDS_NODE,
    NATIVE_DWI_LIST_NODE,
    NATIVE_DWI_MASK_NODE,
    NATIVE_SBREF_DDS_NODE,
    NATIVE_SBREF_LIST_NODE,
    T1_TO_EPI_NODE,
)

DERIVATIVES_DS = [
    #: Native DWI
    (INPUT_NODE, NATIVE_DWI_LIST_NODE, INPUT_TO_NATIVE_DWI_LIST_EDGES),
    (INPUT_NODE, NATIVE_DWI_DDS_NODE, INPUT_TO_NATIVE_DWI_DDS_EDGES),
    (NATIVE_DWI_LIST_NODE, NATIVE_DWI_DDS_NODE, NATIVE_DWI_LIST_TO_DDS_EDGES),
    #: Coreg DWI
    (INPUT_NODE, COREG_DWI_DDS_NODE, INPUT_TO_COREG_DWI_DDS_EDGES),
    (INPUT_NODE, COREG_DWI_LIST_NODE, INPUT_TO_COREG_DWI_LIST_EDGES),
    (COREG_DWI_LIST_NODE, COREG_DWI_DDS_NODE, COREG_DWI_LIST_TO_DDS_EDGES),
    #: Native EPI reference
    (INPUT_NODE, NATIVE_SBREF_LIST_NODE, INPUT_TO_NATIVE_SBREF_LIST_EDGES),
    (INPUT_NODE, NATIVE_SBREF_DDS_NODE, INPUT_TO_NATIVE_SBREF_DDS_EDGES),
    (
        NATIVE_SBREF_LIST_NODE,
        NATIVE_SBREF_DDS_NODE,
        NATIVE_SBREF_LIST_TO_DDS_EDGES,
    ),
    #: Coreg EPI reference
    (INPUT_NODE, COREG_SBREF_LIST_NODE, INPUT_TO_COREG_SBREF_LIST_EDGES),
    (INPUT_NODE, COREG_SBREF_DDS_NODE, INPUT_TO_COREG_SBREF_DDS_EDGES),
    (COREG_SBREF_LIST_NODE, COREG_SBREF_DDS_NODE, COREG_DWI_LIST_TO_DDS_EDGES),
    #: Transformations
    (INPUT_NODE, EPI_TO_T1_NODE, INPUT_TO_EPI_TO_T1_EDGES),
    (INPUT_NODE, T1_TO_EPI_NODE, INPUT_TO_T1_TO_EPI_EDGES),
    # ; Masks
    (INPUT_NODE, NATIVE_DWI_MASK_NODE, INPUT_TO_NATIVE_DWI_MASK_EDGES),
    (INPUT_NODE, COREG_DWI_MASK_NODE, INPUT_TO_COREG_DWI_MASK_EDGES),
]


def init_derivatives_wf(name="dmri_derivatives_wf") -> pe.Workflow:
    """
    Initiates a workflow comprised of a battery of DerivativesDataSinks to store output files in their correct locations.

    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "dmri_derivatives_wf"

    Returns
    -------
    pe.Workflow
        An initiated workflow for storing output files in their correct locations.
    """
    wf = pe.Workflow(name=name)
    wf.connect(DERIVATIVES_DS)
    return wf
