"""
Configurations for *apply_transform* pipelines
"""

INPUT_NODE_FIELDS = [
    "dwi_file",
    "epiref",
    "epi_to_t1w_aff",
    "t1w_brain",
]
OUTPUT_NODE_FIELDS = ["dwi_file"]
TRANSFORM_AFF_KWARGS = dict(flirt_import=True)
DWI_APPLY_XFM_KWARGS = dict()
