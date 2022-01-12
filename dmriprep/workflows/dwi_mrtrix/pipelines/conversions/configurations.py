"""
Configurations for *conversions* pipelines.
"""
LOCATE_JSON_KWARGS = dict(
    input_names=["layout", "image_file"], output_names=["json_file"]
)

MIF_INPUTNODE_FIELDS = [
    # DWI
    "dwi_file",
    "in_bvec",
    "in_bval",
    # Fieldmaps
    "fmap",
]
MIF_OUTPUTNODE_FIELDS = [
    "dwi_file",
    "fmap",
]

NII_INPUTNODE_FIELDS = [
    # DWI
    "dwi_file",
    # fieldmap
    "phasediff",
    # SBRef
    "epi_ref",
]
NII_OUTPUTNODE_FIELDS = [
    "dwi_file",
    "dwi_bvec",
    "dwi_bval",
    "dwi_json",
    "phasediff_file",
    "phasediff_json",
    "epi_ref_file",
    "epi_ref_json",
]
COREG_INPUTNODE_FIELDS = ["coreg_dwi"]
COREG_OUTNODE_FIELDS = [
    "coreg_dwi_file",
    "coreg_dwi_bvec",
    "coreg_dwi_bval",
    "coreg_dwi_json",
]
