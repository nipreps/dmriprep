"""
Connections configurations for *epi_reg* pipelines.
"""

INPUT_TO_EPIREG_EDGES = [
    ("t1w_brain", "t1_brain"),
    ("t1w_head", "t1_head"),
    ("in_file", "epi"),
]
EPIREG_TO_CONVERTXFM_EDGES = [("epi2str_mat", "in_file")]
EPIREG_TO_OUTPUT_EDGES = [
    ("epi2str_mat", "epi_to_t1w_aff"),
    ("out_file", "epi_to_t1w"),
]
CONVERTXFM_TO_OUTPUT_EDGES = [("out_file", "t1w_to_epi_aff")]
