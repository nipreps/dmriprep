"""
Nodes' configurations for *apply_transforms* pipelines.
"""
import nipype.pipeline.engine as pe
from dmriprep.workflows.dwi_mrtrix.pipelines.apply_transform.configurations import (
    APPLY_XFM_MASK_KWARGS,
    DWI_APPLY_XFM_KWARGS,
    INPUT_NODE_FIELDS,
    OUTPUT_NODE_FIELDS,
    RESAMPLE_MASK_KWARGS,
    TRANSFORM_AFF_KWARGS,
)
from nipype.interfaces import ants, fsl
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
TRANSFORM_FSL_AFF_TO_MRTRIX = pe.Node(
    mrt.TransformFSLConvert(**TRANSFORM_AFF_KWARGS), name="transformconvert"
)
APPLY_XFM_DWI_NODE = pe.Node(
    mrt.MRTransform(**DWI_APPLY_XFM_KWARGS), name="apply_xfm_dwi"
)

RESAMPLE_MASK_NODE = pe.Node(
    ants.ApplyTransforms(**RESAMPLE_MASK_KWARGS), name="resample_mask"
)
APPLY_XFM_MASK_NODE = pe.Node(
    fsl.ApplyXFM(**APPLY_XFM_MASK_KWARGS), name="apply_xfm_mask"
)
