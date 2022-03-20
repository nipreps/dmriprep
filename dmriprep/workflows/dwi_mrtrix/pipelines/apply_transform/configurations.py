"""
Configurations for *apply_transform* pipelines
"""

INPUT_NODE_FIELDS = [
    "tensor_metrics",
    "dwi_file",
    "epiref",
    "epi_to_t1w_aff",
    "t1w_brain",
]
OUTPUT_NODE_FIELDS = ["tensor_metrics", "dwi_file"]
TRANSFORM_AFF_KWARGS = dict(flirt_import=True)
TENSOR_APPLY_XFM_KWARGS = dict(apply_xfm=True)
DWI_APPLY_XFM_KWARGS = dict()
