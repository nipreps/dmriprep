from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import fsl
from dwiprep.workflows.coreg.pipelines.epi_reg.nodes import (
    INPUT_NODE,
    OUTPUT_NODE,
    EPIREG_NODE,
    CONVERTXFM_NODE,
)
from dwiprep.workflows.coreg.pipelines.epi_reg.edges import (
    INPUT_TO_EPIREG_EDGES,
    EPIREG_TO_CONVERTXFM_EDGES,
    EPIREG_TO_OUTPUT_EDGES,
    CONVERTXFM_TO_OUTPUT_EDGES,
)

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
