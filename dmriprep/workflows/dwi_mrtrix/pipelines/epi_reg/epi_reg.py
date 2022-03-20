from dmriprep.workflows.dwi_mrtrix.pipelines.epi_reg.edges import (
    CONVERTXFM_TO_OUTPUT_EDGES,
    EPIREG_TO_CONVERTXFM_EDGES,
    EPIREG_TO_OUTPUT_EDGES,
    INPUT_TO_EPIREG_EDGES,
)
from dmriprep.workflows.dwi_mrtrix.pipelines.epi_reg.nodes import (
    CONVERTXFM_NODE,
    EPIREG_NODE,
    INPUT_NODE,
    OUTPUT_NODE,
)
from nipype.interfaces import fsl
from nipype.interfaces import utility as niu
from nipype.pipeline import engine as pe

EPI_REG = [
    (INPUT_NODE, EPIREG_NODE, INPUT_TO_EPIREG_EDGES),
    (EPIREG_NODE, CONVERTXFM_NODE, EPIREG_TO_CONVERTXFM_EDGES),
    (EPIREG_NODE, OUTPUT_NODE, EPIREG_TO_OUTPUT_EDGES),
    (CONVERTXFM_NODE, OUTPUT_NODE, CONVERTXFM_TO_OUTPUT_EDGES),
]


def init_epireg_wf(
    name="epi_reg_wf",
) -> pe.Workflow:
    """
    Initiates a FSL's epi_reg-based workflow to coregister EPI images to structural ones.

    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "epi_reg_wf"

    Returns
    -------
    pe.Workflow
        An initiated workflow for coregistering EPI images to structural ones.
    """
    wf = pe.Workflow(name=name)
    wf.connect(EPI_REG)
    return wf
