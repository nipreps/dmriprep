"""
Nodes' configurations for *preprocessing* pipelines.
"""
import nipype.pipeline.engine as pe
from dmriprep.workflows.dwi_mrtrix.pipelines.preprocess.configurations import (
    BIASCORRECT_KWARGS,
    DWIDENOISE_KWARGS,
    DWIFSLPREPROC_KWARGS,
    INFER_PE_KWARGS,
    INPUT_NODE_FIELDS,
    OUTPUT_NODE_FIELDS,
)
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu


# define function for phase direction inference
def infer_phase_encoding_direction_mif(in_file: str) -> str:
    """
    Utilizes *mrinfo* for a specific query of phase encoding direction.

    Parameters
    ----------
    in_file : str
        File to query

    Returns
    -------
    str
        Phase Encoding Direction as denoted in *in_file*`s header.
    """
    import subprocess

    return (
        subprocess.check_output(
            ["mrinfo", str(in_file), "-property", "PhaseEncodingDirection"]
        )
        .decode("utf-8")
        .replace("\n", "")
    )


#: i/o
INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=INPUT_NODE_FIELDS),
    name="inputnode",
)
OUTPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=OUTPUT_NODE_FIELDS),
    name="outputnode",
)

#: Building blocks
INFER_PE_NODE = pe.Node(
    niu.Function(
        **INFER_PE_KWARGS, function=infer_phase_encoding_direction_mif
    ),
    name="infer_pe",
)

DENOISE_NODE = pe.Node(
    mrt.DWIDenoise(**DWIDENOISE_KWARGS),
    name="denoise",
)

DWIPREPROC_NODE = pe.Node(
    mrt.DWIPreproc(**DWIFSLPREPROC_KWARGS), name="dwipreproc"
)

BIASCORRECT_NODE = pe.Node(
    mrt.DWIBiasCorrect(**BIASCORRECT_KWARGS), name="biascorrect"
)
NII_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(
        out_file="dwi.nii.gz",
        out_bvec="dwi.bvec",
        out_bval="dwi.bval",
        json_export="dwi.json",
    ),
    name="native_dwi_conversion",
)
