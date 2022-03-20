import nipype.pipeline.engine as pe
from dmriprep.workflows.dwi_mrtrix.pipelines.conversions.nii_conversions.configurations import (
    INPUTNODE_FIELDS,
    OUTPUTNODE_FIELDS,
)
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu

INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=INPUTNODE_FIELDS),
    name="inputnode",
)
OUTPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=OUTPUTNODE_FIELDS),
    name="outputnode",
)
NATIVE_DWI_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(
        out_file="dwi.nii.gz",
        out_bvec="dwi.bvec",
        out_bval="dwi.bval",
        json_export="dwi.json",
    ),
    name="native_dwi_conversion",
)
COREG_DWI_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(
        out_file="dwi.nii.gz",
        out_bvec="dwi.bvec",
        out_bval="dwi.bval",
        json_export="dwi.json",
    ),
    name="coreg_dwi_conversion",
)
NATIVE_REFERENCE_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(out_file="dwiref.nii.gz", json_export="dwiref.json"),
    name="native_reference_conversion",
)
COREG_REFERENCE_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(out_file="dwiref.nii.gz", json_export="dwiref.json"),
    name="coreg_reference_conversion",
)
