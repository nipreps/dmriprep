"""
Nodes' configurations for *epi_ref* pipelines.
"""
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import mrtrix3 as mrt

from dwiprep.workflows.dmri.pipelines.epi_ref.configurations import (
    INPUT_NODE_FIELDS,
    OUTPUT_NODE_FIELDS,
    DWIEXTRACT_KWARGS,
    MRMATH_KWARGS,
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
DWIEXTRACT_NODE = pe.Node(
    mrt.DWIExtract(**DWIEXTRACT_KWARGS), name="dwiextract"
)

MRMATH_NODE = pe.Node(
    mrt.MRMath(**MRMATH_KWARGS),
    name="mrmath",
)
