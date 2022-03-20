INPUT_NODE_FIELDS = [
    "source_file",
    "base_directory",
    "native_dwi_preproc_file",
    "native_dwi_preproc_json",
    "native_dwi_preproc_bvec",
    "native_dwi_preproc_bval",
    "native_epi_ref_file",
    "native_epi_ref_json",
    "epi_to_t1w_aff",
    "t1w_to_epi_aff",
    "coreg_dwi_preproc_file",
    "coreg_dwi_preproc_bvec",
    "coreg_dwi_preproc_bval",
    "coreg_dwi_preproc_json",
    "coreg_epi_ref_file",
    "coreg_epi_ref_json",
]

NATIVE_DWI_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="dwi",
    desc="preproc",
    suffix="dwi",
    compress=None,
)
COREG_DWI_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="T1w",
    desc="preproc",
    suffix="dwi",
    compress=None,
)
NATIVE_SBREF_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="dwi",
    desc="preproc",
    suffix="epiref",
    compress=None,
)
COREG_SBREF_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="T1w",
    desc="preproc",
    suffix="epiref",
    compress=None,
)
EPI_TO_T1_AFF_KWARGS = dict(
    datatype="dwi",
    suffix="xfm",
    extension=".txt",
    to="T1w",
    compress=False,
)
EPI_TO_T1_AFF_KWARGS["from"] = "dwi"

T1_to_EPI_AFF_KWARGS = dict(
    datatype="dwi",
    suffix="xfm",
    extension=".txt",
    to="dwi",
    compress=False,
)
T1_to_EPI_AFF_KWARGS["from"] = "T1w"
