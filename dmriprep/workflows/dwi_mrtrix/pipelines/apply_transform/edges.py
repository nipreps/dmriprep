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
