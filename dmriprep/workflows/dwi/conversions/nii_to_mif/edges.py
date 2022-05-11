INPUT_TO_DWI_CONVERSION_EDGES = [("dwi_file", "in_file")]
INPUT_TO_FMAP_CONVERSION_EDGES = [("fmap_file", "in_file")]
LOCATE_ASSOCIATED_TO_COVERSION_EDGES = [
    ("json_file", "json_import"),
    ("bvec_file", "in_bvec"),
    ("bval_file", "in_bval"),
]

DWI_CONVERSION_TO_OUTPUT_EDGES = [("out_file", "dwi_file")]
FMAP_CONVERSION_TO_OUTPUT_EDGES = [("out_file", "fmap_file")]
