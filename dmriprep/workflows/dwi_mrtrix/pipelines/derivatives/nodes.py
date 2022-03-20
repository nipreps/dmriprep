import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu

from dwiprep.interfaces.dds import DerivativesDataSink
from dwiprep.workflows.dmri.pipelines.derivatives.configurations import (
    COREG_DWI_PREPROC_KWARGS,
    COREG_SBREF_PREPROC_KWARGS,
    COREG_TENSOR_KWARGS,
    EPI_TO_T1_AFF_KWARGS,
    INPUT_NODE_FIELDS,
    NATIVE_DWI_PREPROC_KWARGS,
    NATIVE_SBREF_PREPROC_KWARGS,
    NATIVE_TENSOR_KWARGS,
    PHASEDIFF_KWARGS,
    T1_to_EPI_AFF_KWARGS,
)


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

#: phasediff
PHASEDIFF_LIST_NODE = pe.Node(
    niu.Merge(numinputs=2), name="list_phasediff_inputs"
)
PHASEDIFF_DDS_NODE = pe.MapNode(
    DerivativesDataSink(**PHASEDIFF_KWARGS),
    name="ds_phasediff",
    iterfield=["in_file"],
)

#: DWI
NATIVE_DWI_LIST_NODE = pe.Node(
    niu.Merge(numinputs=4), name="list_native_dwi_inputs"
)
NATIVE_DWI_DDS_NODE = pe.MapNode(
    DerivativesDataSink(**NATIVE_DWI_PREPROC_KWARGS),
    name="ds_native_dwi",
    iterfield=["in_file"],
)

COREG_DWI_LIST_NODE = pe.Node(
    niu.Merge(numinputs=4), name="list_coreg_dwi_inputs"
)
COREG_DWI_DDS_NODE = pe.MapNode(
    DerivativesDataSink(**COREG_DWI_PREPROC_KWARGS),
    name="ds_coreg_dwi",
    iterfield=["in_file"],
)

#: EPI reference
NATIVE_SBREF_LIST_NODE = pe.Node(
    niu.Merge(numinputs=2), name="list_native_sbref_inputs"
)
NATIVE_SBREF_DDS_NODE = pe.MapNode(
    DerivativesDataSink(**NATIVE_SBREF_PREPROC_KWARGS),
    name="ds_native_sbref",
    iterfield=["in_file"],
)

COREG_SBREF_DDS_NODE = pe.MapNode(
    DerivativesDataSink(**COREG_SBREF_PREPROC_KWARGS),
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

#: tensor-derived
NATIVE_INFER_METRIC_NODE = pe.MapNode(
    niu.Function(
        input_names=["in_file"],
        output_names=["metric", "in_file"],
        function=infer_metric,
    ),
    name="native_infer_metric",
    iterfield=["in_file"],
)
NATIVE_TENSOR_NODE = pe.MapNode(
    DerivativesDataSink(**NATIVE_TENSOR_KWARGS),
    name="ds_native_tensor",
    iterfield=["in_file", "desc"],
)
NATIVE_TENSOR_WF = pe.Workflow(name="ds_native_tensor_wf")
NATIVE_TENSOR_WF.connect(
    [
        (
            NATIVE_INFER_METRIC_NODE,
            NATIVE_TENSOR_NODE,
            [("metric", "desc"), ("in_file", "in_file")],
        ),
    ]
)
COREG_INFER_METRIC_NODE = pe.MapNode(
    niu.Function(
        input_names=["in_file"],
        output_names=["metric", "in_file"],
        function=infer_metric,
    ),
    name="coreg_infer_metric",
    iterfield=["in_file"],
)
COREG_TENSOR_NODE = pe.MapNode(
    DerivativesDataSink(**COREG_TENSOR_KWARGS),
    name="ds_coreg_tensor",
    iterfield=["in_file", "desc"],
)
COREG_TENSOR_WF = pe.Workflow(name="ds_coreg_tensor_wf")
COREG_TENSOR_WF.connect(
    [
        (
            COREG_INFER_METRIC_NODE,
            COREG_TENSOR_NODE,
            [("metric", "desc"), ("in_file", "in_file")],
        ),
    ]
)
