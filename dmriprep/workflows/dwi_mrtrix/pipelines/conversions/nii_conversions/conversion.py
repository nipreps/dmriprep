import nipype.pipeline.engine as pe
from dmriprep.workflows.dwi_mrtrix.pipelines.conversions.nii_conversions.edges import (
    COREG_DWI_TO_OUTPUT_EDGES,
    INPUT_TO_COREG_DWI_EDGES,
    INPUT_TO_NATIVE_DWI_EDGES,
    NATIVE_DWI_TO_OUTPUT_EDGES,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.conversions.nii_conversions.nodes import (
    COREG_DWI_CONVERSION_NODE,
    INPUT_NODE,
    NATIVE_DWI_CONVERSION_NODE,
    OUTPUT_NODE,
)

NII_CONVERSION = [
    (INPUT_NODE, NATIVE_DWI_CONVERSION_NODE, INPUT_TO_NATIVE_DWI_EDGES),
    (INPUT_NODE, COREG_DWI_CONVERSION_NODE, INPUT_TO_COREG_DWI_EDGES),
    (NATIVE_DWI_CONVERSION_NODE, OUTPUT_NODE, NATIVE_DWI_TO_OUTPUT_EDGES),
    (COREG_DWI_CONVERSION_NODE, OUTPUT_NODE, COREG_DWI_TO_OUTPUT_EDGES),
]


def init_nii_conversion_wf(name: str = "nii_conversion_wf") -> pe.Workflow:
    """
    Initiate a workflow to convert input files to NIfTI format for ease of use


    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "nii_conversion_wf"

    Returns
    -------
    pe.Workflow
        A NIfTI conversion workflow
    """
    wf = pe.Workflow(name=name)
    wf.connect(NII_CONVERSION)
    return wf
