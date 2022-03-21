INPUT_TO_NATIVE_DWI_EDGES = [("native_preproc_dwi", "in_file")]
INPUT_TO_COREG_DWI_EDGES = [("coreg_preproc_dwi", "in_file")]

NATIVE_DWI_TO_OUTPUT_EDGES = [
    ("out_file", "native_dwi_file"),
    ("out_bvec", "native_dwi_bvec"),
    ("out_bval", "native_dwi_bval"),
    ("json_export", "native_dwi_json"),
]
COREG_DWI_TO_OUTPUT_EDGES = [
    ("out_file", "coreg_dwi_file"),
    ("out_bvec", "coreg_dwi_bvec"),
    ("out_bval", "coreg_dwi_bval"),
    ("json_export", "coreg_dwi_json"),
]
