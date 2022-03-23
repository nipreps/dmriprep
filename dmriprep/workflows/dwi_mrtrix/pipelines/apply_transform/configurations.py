"""
Configurations for *apply_transform* pipelines
"""

INPUT_NODE_FIELDS = [
    "dwi_file",
    "dwi_reference",
    "epi_to_t1w_aff",
    "t1w_to_epi_aff",
    "t1w_brain",
    "t1w_mask",
]
OUTPUT_NODE_FIELDS = ["dwi_file", "native_dwi_mask", "coreg_dwi_mask"]
TRANSFORM_AFF_KWARGS = dict(flirt_import=True)
DWI_APPLY_XFM_KWARGS = dict()
APPLY_XFM_MASK_KWARGS = dict(
    apply_xfm=True, interp="nearestneighbour", out_file="mask.nii.gz"
)
RESAMPLE_MASK_KWARGS = dict(
    interpolation="NearestNeighbor",
    output_image="mask.nii.gz",
    transforms="identity",
)
