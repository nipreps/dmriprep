INPUTNODE_FIELDS = [
    # Native DWI
    "native_preproc_dwi",
    # Native reference
    "native_dwi_reference",
    # Coreg DWI
    "coreg_preproc_dwi",
    # Coreg reference
    "coreg_dwi_reference",
]
OUTPUTNODE_FIELDS = [
    "native_dwi_file",
    "native_dwi_bvec",
    "native_dwi_bval",
    "native_dwi_json",
    "native_reference_file",
    "native_reference_json",
    "coreg_dwi_file",
    "coreg_dwi_bvec",
    "coreg_dwi_bval",
    "coreg_dwi_json",
    "coreg_reference_file",
    "coreg_reference_json",
]
