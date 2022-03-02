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
