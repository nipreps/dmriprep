"""
Connections configurations for *conversions* pipelines.
"""

#: Conversion to mif
MIF_INPUT_TO_DWI_CONVERSION_EDGES = [
    ("dwi_file", "in_file"),
    ("dwi_json", "json_import"),
    ("in_bvec", "in_bvec"),
    ("in_bval", "in_bval"),
]
MIF_DWI_CONVERSION_TO_OUTPUT_EDGES = [("out_file", "dwi_file")]

MIF_INPUT_TO_FMAP_AP_CONVERSION_EDGES = [
    ("fmap_ap", "in_file"),
    ("fmap_ap_json", "json_import"),
]
MIF_FMAP_AP_CONVERSION_TO_OUTPUT_EDGES = [("out_file", "fmap_ap")]

MIF_INPUT_TO_FMAP_PA_CONVERSION_EDGES = [
    ("fmap_pa", "in_file"),
    ("fmap_pa_json", "json_import"),
]
MIF_FMAP_PA_CONVERSION_TO_OUTPUT_EDGES = [("out_file", "fmap_pa")]

#: Conversion to MIfTI
NII_INPUT_TO_PREPROC_DWI_CONVERSION_EDGES = [
    ("dwi_file", "in_file"),
]
NII_INPUT_TO_COREG_DWI_CONVERSION_EDGES = [
    ("coreg_dwi", "in_file"),
]

NII_INPUT_TO_PREPROC_SBREF_CONVERSION_EDGES = [
    ("epi_ref", "in_file"),
]

NII_INPUT_TO_PHASEDIFF_CONVERSION_EDGES = [("phasediff", "in_file")]
NII_PREPROC_DWI_CONVERSION_TO_OUTPUT_EDGES = [
    ("out_file", "dwi_file"),
    ("out_bvec", "dwi_bvec"),
    ("out_bval", "dwi_bval"),
    ("json_export", "dwi_json"),
]
NII_COREG_DWI_CONVERSION_TO_OUTPUT_EDGES = [
    ("out_file", "coreg_dwi_file"),
    ("out_bvec", "coreg_dwi_bvec"),
    ("out_bval", "coreg_dwi_bval"),
    ("json_export", "coreg_dwi_json"),
]
NII_PREPROC_SBREF_CONVERSION_TO_OUTPUT_EDGES = [
    ("out_file", "epi_ref_file"),
    ("json_export", "epi_ref_json"),
]
NII_PHASEDIFF_CONVERSION_TO_OUTPUT_EDGES = [
    ("out_file", "phasediff_file"),
    ("json_export", "phasediff_json"),
]
