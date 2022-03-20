"""
Configurations for *epi_ref* pipeline.
"""
#: i/o
INPUT_NODE_FIELDS = ["dwi_file"]
OUTPUT_NODE_FIELDS = ["epi_ref_file"]

#: Keyword arguments
DWIEXTRACT_KWARGS = dict(bzero=True, out_file="b0.mif")
MRMATH_KWARGS = dict(operation="mean", axis=3, out_file="mean_b0.mif")
