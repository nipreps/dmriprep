import nipype.pipeline.engine as pe
from traits.trait_base import _Undefined

from dwiprep.workflows.dmri.pipelines.conversions.edges import (
    MIF_DWI_CONVERSION_TO_OUTPUT_EDGES,
    MIF_FMAP_AP_CONVERSION_TO_OUTPUT_EDGES,
    MIF_FMAP_PA_CONVERSION_TO_OUTPUT_EDGES,
    MIF_INPUT_TO_DWI_CONVERSION_EDGES,
    MIF_INPUT_TO_FMAP_AP_CONVERSION_EDGES,
    MIF_INPUT_TO_FMAP_PA_CONVERSION_EDGES,
    NII_COREG_DWI_CONVERSION_TO_OUTPUT_EDGES,
    NII_INPUT_TO_COREG_DWI_CONVERSION_EDGES,
    NII_INPUT_TO_PHASEDIFF_CONVERSION_EDGES,
    NII_INPUT_TO_PREPROC_DWI_CONVERSION_EDGES,
    NII_INPUT_TO_PREPROC_SBREF_CONVERSION_EDGES,
    NII_PHASEDIFF_CONVERSION_TO_OUTPUT_EDGES,
    NII_PREPROC_DWI_CONVERSION_TO_OUTPUT_EDGES,
    NII_PREPROC_SBREF_CONVERSION_TO_OUTPUT_EDGES,
)
from dwiprep.workflows.dmri.pipelines.conversions.nodes import (
    COREG_INPUT_NODE,
    COREG_OUTPUT_NODE,
    MIF_DWI_CONVERSION_NODE,
    MIF_FMAP_AP_CONVERSION_NODE,
    MIF_FMAP_PA_CONVERSION_NODE,
    MIF_INPUT_NODE,
    MIF_OUTPUT_NODE,
    NII_COREG_DWI_CONVERSION_NODE,
    NII_INPUT_NODE,
    NII_OUTPUT_NODE,
    NII_PHASEDIFF_CONVERSION_NODE,
    NII_PREPROC_DWI_CONVERSION_NODE,
    NII_PREPROC_SBREF_CONVERSION_NODE,
)

#: Conversion from NIfTI to .mif format.
MIF_DWI_CONVERSION = [
    (
        MIF_INPUT_NODE,
        MIF_DWI_CONVERSION_NODE,
        MIF_INPUT_TO_DWI_CONVERSION_EDGES,
    ),
    (
        MIF_DWI_CONVERSION_NODE,
        MIF_OUTPUT_NODE,
        MIF_DWI_CONVERSION_TO_OUTPUT_EDGES,
    ),
]

MIF_FMAP_AP_CONVERSION = [
    (
        MIF_INPUT_NODE,
        MIF_FMAP_AP_CONVERSION_NODE,
        MIF_INPUT_TO_FMAP_AP_CONVERSION_EDGES,
    ),
    (
        MIF_FMAP_AP_CONVERSION_NODE,
        MIF_OUTPUT_NODE,
        MIF_FMAP_AP_CONVERSION_TO_OUTPUT_EDGES,
    ),
]
MIF_FMAP_PA_CONVERSION = [
    (
        MIF_INPUT_NODE,
        MIF_FMAP_PA_CONVERSION_NODE,
        MIF_INPUT_TO_FMAP_PA_CONVERSION_EDGES,
    ),
    (
        MIF_FMAP_PA_CONVERSION_NODE,
        MIF_OUTPUT_NODE,
        MIF_FMAP_PA_CONVERSION_TO_OUTPUT_EDGES,
    ),
]

#: Conversion from .mif to NIfTI format
NII_CONVERSION = [
    (
        NII_INPUT_NODE,
        NII_PREPROC_DWI_CONVERSION_NODE,
        NII_INPUT_TO_PREPROC_DWI_CONVERSION_EDGES,
    ),
    (
        NII_INPUT_NODE,
        NII_PHASEDIFF_CONVERSION_NODE,
        NII_INPUT_TO_PHASEDIFF_CONVERSION_EDGES,
    ),
    (
        NII_INPUT_NODE,
        NII_PREPROC_SBREF_CONVERSION_NODE,
        NII_INPUT_TO_PREPROC_SBREF_CONVERSION_EDGES,
    ),
    (
        NII_PREPROC_DWI_CONVERSION_NODE,
        NII_OUTPUT_NODE,
        NII_PREPROC_DWI_CONVERSION_TO_OUTPUT_EDGES,
    ),
    (
        NII_PHASEDIFF_CONVERSION_NODE,
        NII_OUTPUT_NODE,
        NII_PHASEDIFF_CONVERSION_TO_OUTPUT_EDGES,
    ),
    (
        NII_PREPROC_SBREF_CONVERSION_NODE,
        NII_OUTPUT_NODE,
        NII_PREPROC_SBREF_CONVERSION_TO_OUTPUT_EDGES,
    ),
]

COREG_NII_CONVERSION = [
    (
        COREG_INPUT_NODE,
        NII_COREG_DWI_CONVERSION_NODE,
        NII_INPUT_TO_COREG_DWI_CONVERSION_EDGES,
    ),
    (
        NII_COREG_DWI_CONVERSION_NODE,
        NII_OUTPUT_NODE,
        NII_COREG_DWI_CONVERSION_TO_OUTPUT_EDGES,
    ),
]


def init_conversion_wf(
    main_inputs: pe.Node, name: str = "mif_conversion_wf"
) -> pe.Workflow:
    """
    Initiate a workflow to convert input files to mif format for better compatability with *mrtrix3* functions

    Parameters
    ----------
    main_inputs : pe.Node
        Main workflow's input node
    name : str, optional
        Conversion workflow name, by default "mif_conversion_wf"

    Returns
    -------
    pe.Workflow
        A mif conversion workflow
    """
    wf = pe.Workflow(name=name)
    wf.connect(MIF_DWI_CONVERSION)
    if not isinstance(getattr(main_inputs.inputs, "fmap_ap"), _Undefined):
        wf.connect(MIF_FMAP_AP_CONVERSION)
    if not isinstance(getattr(main_inputs.inputs, "fmap_pa"), _Undefined):
        wf.connect(MIF_FMAP_PA_CONVERSION)
    return wf


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

def init_coreg_conversion_wf(name: str = "coreg_conversion_wf") -> pe.Workflow:
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
