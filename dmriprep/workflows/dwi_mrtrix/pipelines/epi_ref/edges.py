"""
Connections configurations for *epi_ref* pipelines.
"""

INPUT_TO_DWIEXTRACT_EDGES = [
    ("dwi_file", "in_file"),
]
DWIEXTRACT_TO_MRMATH_EDGES = [("out_file", "in_file")]

MRMATH_TO_OUTPUT_EDGES = [("out_file", "epi_ref_file")]
