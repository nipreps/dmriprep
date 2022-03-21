INPUTNODE_FIELDS = [
    # Native DWI
    "native_preproc_dwi",
    # Coreg DWI
    "coreg_preproc_dwi",
]
OUTPUTNODE_FIELDS = [
    "native_dwi_file",
    "native_dwi_bvec",
    "native_dwi_bval",
    "native_dwi_json",
    "coreg_dwi_file",
    "coreg_dwi_bvec",
    "coreg_dwi_bval",
    "coreg_dwi_json",
]

NATIVE_DWI_CONVERSION_KWARGS = dict(
    out_file="dwi.nii.gz",
    out_bvec="dwi.bvec",
    out_bval="dwi.bval",
    json_export="dwi.json",
)

COREG_DWI_CONVERSION_KWARGS = dict(
    out_file="dwi.nii.gz",
    out_bvec="dwi.bvec",
    out_bval="dwi.bval",
    json_export="dwi.json",
)
