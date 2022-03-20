"""
Configurations for *epi_reg* pipeline.
"""
#: i/o
INPUT_NODE_FIELDS = ["in_file", "t1w_brain", "t1w_head"]
OUTPUT_NODE_FIELDS = ["epi_to_t1w_aff", "t1w_to_epi_aff", "epi_to_t1w"]

#: Keyword arguments
EPIREG_KWARGS = dict()
CONVERTXFM_KWARGS = dict(invert_xfm=True)
