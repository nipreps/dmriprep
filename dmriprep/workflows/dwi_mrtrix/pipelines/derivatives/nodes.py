import nipype.pipeline.engine as pe

# from dwiprep.interfaces.dds import DerivativesDataSink
from dmriprep.interfaces import DerivativesDataSink
from dmriprep.workflows.dwi_mrtrix.pipelines.derivatives.configurations import (
    COREG_DWI_KWARGS,
    COREG_DWI_MASK_KWARGS,
    COREG_SBREF_KWARGS,
    EPI_TO_T1_AFF_KWARGS,
    INPUT_NODE_FIELDS,
    NATIVE_DWI_KWARGS,
    NATIVE_DWI_MASK_KWARGS,
    NATIVE_SBREF_KWARGS,
    T1_to_EPI_AFF_KWARGS,
)
from nipype.interfaces import utility as niu


def infer_metric(in_file: str) -> str:
    """
    A simple function to infer tensor-derived metric from file's name.

    Parameters
    ----------
    in_file : str
        A string representing an existing file.

    Returns
    -------
    str
        A metric identifier/label for BIDS specification (i.e, fa, adc, rd etc.)
    """
    from pathlib import Path

    file_name = Path(in_file).name
    suffix = file_name.split(".")[0].lower()
    if "_" in suffix:
        suffix = suffix.split("_")[0]
    return suffix, in_file


INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=INPUT_NODE_FIELDS), name="inputnode"
)


#: DWI
NATIVE_DWI_LIST_NODE = pe.Node(
    niu.Merge(numinputs=4), name="list_native_dwi_inputs"
)
NATIVE_DWI_DDS_NODE = pe.MapNode(
    DerivativesDataSink(**NATIVE_DWI_KWARGS),
    name="ds_native_dwi",
    iterfield=["in_file"],
)

COREG_DWI_LIST_NODE = pe.Node(
    niu.Merge(numinputs=4), name="list_coreg_dwi_inputs"
)
COREG_DWI_DDS_NODE = pe.MapNode(
    DerivativesDataSink(**COREG_DWI_KWARGS),
    name="ds_coreg_dwi",
    iterfield=["in_file"],
)

#: EPI reference
NATIVE_SBREF_LIST_NODE = pe.Node(
    niu.Merge(numinputs=2), name="list_native_sbref_inputs"
)
NATIVE_SBREF_DDS_NODE = pe.MapNode(
    DerivativesDataSink(**NATIVE_SBREF_KWARGS),
    name="ds_native_sbref",
    iterfield=["in_file"],
)
COREG_SBREF_LIST_NODE = pe.Node(
    niu.Merge(numinputs=2), name="list_coreg_sbref_inputs"
)
COREG_SBREF_DDS_NODE = pe.MapNode(
    DerivativesDataSink(**COREG_SBREF_KWARGS),
    name="ds_coreg_sbref",
    iterfield=["in_file"],
)

#: transformations
EPI_TO_T1_NODE = pe.Node(
    DerivativesDataSink(**EPI_TO_T1_AFF_KWARGS),
    name="ds_epi_to_t1_aff",
)
T1_TO_EPI_NODE = pe.Node(
    DerivativesDataSink(**T1_to_EPI_AFF_KWARGS),
    name="ds_t1_to_epi_aff",
)

NATIVE_DWI_MASK_NODE = pe.Node(
    DerivativesDataSink(**NATIVE_DWI_MASK_KWARGS), name="ds_native_dwi_mask"
)
COREG_DWI_MASK_NODE = pe.Node(
    DerivativesDataSink(**COREG_DWI_MASK_KWARGS), name="ds_coreg_dwi_mask"
)
