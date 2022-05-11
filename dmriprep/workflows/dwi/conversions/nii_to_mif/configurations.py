"""
Configuration file for nii_to_mif.py
"""

#: i/o
INPUT_NODE_FIELDS = ["dwi_file", "fmap_file"]
OUTPUT_NODE_FIELDS = ["dwi_file", "fmap_file"]

#: Keyword arguments
LOCATE_ASSOCIATED_KWARGS = dict(
    input_names=["in_file"],
    output_names=["json_file", "bvec_file", "bval_file"],
)
