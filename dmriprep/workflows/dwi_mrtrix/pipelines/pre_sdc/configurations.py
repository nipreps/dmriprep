"""
Configurations for *pre_sdc* pipeline.
"""
#: i/o
INPUT_NODE_FIELDS = ["dwi_file", "fmap"]
OUTPUT_NODE_FIELDS = ["merged_phasediff"]

#: Keyword arguments
DWIEXTRACT_KWARGS = dict(bzero=True)
MRMATH_KWARGS = dict(operation="mean", axis=3)
MERGE_KWARGS = dict(numinputs=2)
MRCAT_KWARGS = dict(axis=3)
