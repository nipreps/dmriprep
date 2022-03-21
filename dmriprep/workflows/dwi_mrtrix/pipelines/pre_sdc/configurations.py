"""
Configurations for *pre_sdc* pipeline.
"""
#: i/o
INPUT_NODE_FIELDS = ["dwi_file", "fmap"]
OUTPUT_NODE_FIELDS = ["merged_phasediff", "dwi_reference"]

#: Keyword arguments
DWIEXTRACT_KWARGS = dict(bzero=True, out_file="b0.mif")
MRMATH_KWARGS = dict(operation="mean", axis=3, out_file="mean_b0.nii.gz")
MERGE_KWARGS = dict(numinputs=2)
MRCAT_KWARGS = dict(axis=3)
