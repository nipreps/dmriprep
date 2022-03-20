import nipype.pipeline.engine as pe
from dmriprep.workflows.dwi_mrtrix.pipelines.conversions.mif_conversions.edges import (
    MIF_DWI_CONVERSION_TO_OUTPUT_EDGES,
    MIF_FMAP_CONVERSION_TO_OUTPUT_EDGES,
    MIF_INPUT_TO_DWI_CONVERSION_EDGES,
    MIF_INPUT_TO_FMAP_CONVERSION_EDGES,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.conversions.mif_conversions.nodes import (
    MIF_DWI_CONVERSION_NODE,
    MIF_FMAP_CONVERSION_NODE,
    MIF_INPUT_NODE,
    MIF_OUTPUT_NODE,
)
from traits.trait_base import _Undefined

#: Conversion from NIfTI to .mif format.
MIF_DWI_CONVERSION = [
    (
        MIF_INPUT_NODE,
        MIF_DWI_CONVERSION_NODE,
        MIF_INPUT_TO_DWI_CONVERSION_EDGES,
    ),
    (
        MIF_INPUT_NODE,
        MIF_FMAP_CONVERSION_NODE,
        MIF_INPUT_TO_FMAP_CONVERSION_EDGES,
    ),
    (
        MIF_DWI_CONVERSION_NODE,
        MIF_OUTPUT_NODE,
        MIF_DWI_CONVERSION_TO_OUTPUT_EDGES,
    ),
    (
        MIF_FMAP_CONVERSION_NODE,
        MIF_OUTPUT_NODE,
        MIF_FMAP_CONVERSION_TO_OUTPUT_EDGES,
    ),
]


def init_mif_conversion_wf(name: str = "mif_conversion_wf") -> pe.Workflow:
    """
    Initiate a workflow to convert input files to mif format for better compatability with *mrtrix3* functions

    Parameters
    ----------
    name : str, optional
        Conversion workflow name, by default "mif_conversion_wf"

    Returns
    -------
    pe.Workflow
        A mif conversion workflow
    """
    wf = pe.Workflow(name=name)
    wf.connect(MIF_DWI_CONVERSION)
    return wf
