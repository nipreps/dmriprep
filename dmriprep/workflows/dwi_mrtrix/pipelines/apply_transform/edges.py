"""
Edges' configurations for *apply_transforms* pipelines.
"""
INPUT_TO_DWI_XFM_EDGES = [
    ("dwi_file", "in_files"),
]
INPUT_TO_TRANSFORM_CONVERT_EDGES = [
    ("dwi_reference", "in_file"),
    ("t1w_brain", "reference"),
    ("epi_to_t1w_aff", "in_transform"),
]
TRANSFORM_CONVERT_TO_DWI_XFM_EDGES = [("out_transform", "linear_transform")]
TENSOR_XFM_TO_OUTPUT_EDGES = [("out_file", "tensor_metrics")]
DWI_XFM_TO_OUTPUT_EDGES = [("out_file", "dwi_file")]

INPUT_TO_RESAMPLE_XFM_EDGES = [
    ("t1w_mask", "input_image"),
    ("dwi_reference", "reference_image"),
]
RESAMPLE_MASK_TO_OUTPUT_EDGES = [("output_image", "coreg_dwi_mask")]

INPUT_TO_APPLY_XFM_MASK_EDGES = [
    ("t1w_mask", "in_file"),
    ("t1w_to_epi_aff", "in_matrix_file"),
    ("dwi_reference", "reference"),
]
APPLY_XFM_MASK_TO_OUTPUT_EDGES = [("out_file", "native_dwi_mask")]
