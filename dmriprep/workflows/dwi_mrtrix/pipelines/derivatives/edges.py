#: phasediff
INPUT_TO_PHASEDIFF_LIST_EDGES = [
    ("phasediff_file", "in1"),
    ("phasediff_json", "in2"),
]
INPUT_TO_PHASEDIFF_DDS_EDGES = [
    ("source_file", "source_file"),
    ("base_directory", "base_directory"),
]
PHASEDIFF_LIST_TO_DDS_EDGES = [("out", "in_file")]

#: DWI - native
INPUT_TO_NATIVE_DWI_LIST_EDGES = [
    ("native_dwi_file", "in1"),
    ("native_dwi_json", "in2"),
    ("native_dwi_bvec", "in3"),
    ("native_dwi_bval", "in4"),
]
INPUT_TO_NATIVE_DWI_DDS_EDGES = [
    ("source_file", "source_file"),
    ("base_directory", "base_directory"),
]
NATIVE_DWI_LIST_TO_DDS_EDGES = [("out", "in_file")]

#: DWI - coreg
INPUT_TO_COREG_DWI_LIST_EDGES = [
    ("coreg_dwi_file", "in1"),
    ("coreg_dwi_json", "in2"),
    ("coreg_dwi_bvec", "in3"),
    ("coreg_dwi_bval", "in4"),
]
INPUT_TO_COREG_DWI_DDS_EDGES = [
    ("source_file", "source_file"),
    ("base_directory", "base_directory"),
]
COREG_DWI_LIST_TO_DDS_EDGES = [("out", "in_file")]

#: EPI reference - native
INPUT_TO_NATIVE_SBREF_LIST_EDGES = [
    ("native_epi_ref_file", "in1"),
    ("native_epi_ref_json", "in2"),
]
INPUT_TO_NATIVE_SBREF_DDS_EDGES = [
    ("source_file", "source_file"),
    ("base_directory", "base_directory"),
]
NATIVE_SBREF_LIST_TO_DDS_EDGES = [("out", "in_file")]

#: EPI reference - coreg
INPUT_TO_COREG_SBREF_LIST_EDGES = [
    ("coreg_epi_ref_file", "in1"),
    ("coreg_epi_ref_json", "in2"),
]
INPUT_TO_COREG_SBREF_DDS_EDGES = [
    ("source_file", "source_file"),
    ("base_directory", "base_directory"),
]
COREG_SBREF_LIST_TO_DDS_EDGES = [("out", "in_file")]
#: Transformations
INPUT_TO_EPI_TO_T1_EDGES = [
    ("epi_to_t1w_aff", "in_file"),
    ("source_file", "source_file"),
    ("base_directory", "base_directory"),
]
INPUT_TO_T1_TO_EPI_EDGES = [
    ("t1w_to_epi_aff", "in_file"),
    ("source_file", "source_file"),
    ("base_directory", "base_directory"),
]
INPUT_TO_NATIVE_DWI_MASK_EDGES = [
    ("native_dwi_mask", "in_file"),
    ("source_file", "source_file"),
    ("base_directory", "base_directory"),
]
INPUT_TO_COREG_DWI_MASK_EDGES = [
    ("coreg_dwi_mask", "in_file"),
    ("source_file", "source_file"),
    ("base_directory", "base_directory"),
]
