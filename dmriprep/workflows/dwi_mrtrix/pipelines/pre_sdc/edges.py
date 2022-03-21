"""
Connections configurations for *pre_sdc* pipelines.
"""

#: fieldmap preperation
INPUT_TO_MERGE_EDGES = [("fmap", "in2")]
INPUT_TO_DWIEXTRACT_EDGES = [("dwi_file", "in_file")]
DWIEXTRACT_TO_MRMATH_EDGES = [("out_file", "in_file")]
MRMATH_TO_MERGE_EDGES = [("out_file", "in1")]
MERGE_TO_MRCAT_EDGES = [("out", "in_files")]
MRCAT_TO_OUTPUT_EDGES = [("out_file", "merged_phasediff")]
MRMATH_TO_OUTPUT_EDGES = [("out_file", "dwi_reference")]
