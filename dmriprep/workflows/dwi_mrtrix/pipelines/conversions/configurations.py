"""
Configurations for *conversions* pipelines.
"""

MIF_INPUTNODE_FIELDS = [
    # DWI
    "dwi_file",
    "dwi_json",
    "in_bvec",
    "in_bval",
    # Fieldmaps
    "fmap_file",
    "fmap_json",
]

MIF_OUTPUTNODE_FIELDS = [
    # DWI
    "dwi_file",
    # Fieldmaps
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
