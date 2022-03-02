"""
Nodes' configurations for *fmap_prep* pipelines.
"""
import nipype.pipeline.engine as pe
from dmriprep.workflows.dwi_mrtrix.pipelines.fmap_prep.configurations import (
    DWIEXTRACT_KWARGS,
    INPUT_NODE_FIELDS,
    MERGE_KWARGS,
    MRCAT_KWARGS,
    MRMATH_KWARGS,
    OUTPUT_NODE_FIELDS,
)
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu

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
    mrt.DWIExtract(**DWIEXTRACT_KWARGS), name="extract_b0"
)
MRMATH_NODE = pe.Node(mrt.MRMath(**MRMATH_KWARGS), name="average_b0s")
MERGE_NODE = pe.Node(niu.Merge(**MERGE_KWARGS), name="merge_files")

MRCAT_NODE = pe.Node(
    mrt.MRCat(**MRCAT_KWARGS),
    name="mrcat",
)
