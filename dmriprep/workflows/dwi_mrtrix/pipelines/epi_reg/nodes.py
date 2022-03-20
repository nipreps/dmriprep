"""
Nodes' configurations for *epi_eg* pipelines.
"""
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import fsl

from dwiprep.workflows.coreg.pipelines.epi_reg.configurations import (
    INPUT_NODE_FIELDS,
    OUTPUT_NODE_FIELDS,
    EPIREG_KWARGS,
    CONVERTXFM_KWARGS,
)

#: i/o
INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=INPUT_NODE_FIELDS),
    name="inputnode",
)
OUTPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=OUTPUT_NODE_FIELDS),
    name="outputnode",
)

#: Building blocks
EPIREG_NODE = pe.Node(fsl.EpiReg(**EPIREG_KWARGS), name="epi_reg")

CONVERTXFM_NODE = pe.Node(
    fsl.ConvertXFM(**CONVERTXFM_KWARGS),
    name="invert_xfm",
)
