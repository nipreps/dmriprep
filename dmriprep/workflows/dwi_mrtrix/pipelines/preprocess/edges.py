"""
Connections configurations for *preprocess* pipelines.
"""

#: fieldmap preperation
INPUT_TO_DENOISE_EDGES = [("dwi_file", "in_file")]
INPUT_TO_DWIPREPROC_EDGES = [("merged_phasediff", "in_epi")]
DENOISE_TO_INFER_PE_EDGES = [("out_file", "in_file")]
DENOISE_TO_DWIPREPROC_EDGES = [("out_file", "in_file")]
INFER_PE_TO_DWIPREPROC_EDGES = [("pe_dir", "pe_dir")]
DWIPREPROC_TO_BIASCORRECT_EDGES = [("out_file", "in_file")]
BIASCORRECT_TO_OUTPUT_EDGES = [("out_file", "dwi_preproc")]
BIASCORRECT_TO_CONVERSION_EDGES = [("out_file", "in_file")]
CONVERSION_TO_OUTPUT_DEGES = [
    ("out_file", "preproc_dwi_file"),
    ("out_bvec", "preproc_dwi_bvec"),
    ("out_bval", "preproc_dwi_bval"),
    ("json_export", "preproc_dwi_json"),
]
