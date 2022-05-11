"""
Nodes' configurations for *fieldmap_query* workflow
"""
import nipype.pipeline.engine as pe
from dmriprep.workflows.dwi.fieldmap_query.configurations import (
    OPPOSITE_PHASE_QUERY_KWARGS,
)
from nipype.interfaces import utility as niu


def locate_opposite_phase(dwi_file: str):
    """
    Locates

    Parameters
    ----------
    dwi_file : str
        _description_
    """
    from bids.layout import parse_file_entities
    from dmriprep.config import config
    from dmriprep.workflows.dwi.fieldmap_query.utils import check_opposite

    layout = config.execution.layout
    # Parse entities from dwi_file
    entities = parse_file_entities(dwi_file)
    _ = entities.pop("direction", None)
    # Query DWI file's phase direction
    direction = layout.get_metadata(dwi_file).get("PhaseEncodingDirection")
    # Check if opposite phase DWI is available
    available_dwis = layout.get("file", **entities)
    available_dwis.remove(str(dwi_file))
    opposite_dwis = []
    for dwi in available_dwis:
        if check_opposite(direction, dwi, layout):
            opposite_dwis.append(dwi)
    if len(opposite_dwis) == 1:
        return opposite_dwis[0]
    elif len(opposite_dwis) > 1:
        config.logger.warning(
            """Located more than one opposite phase DWI.
            Will use the first one."""
        )
        return opposite_dwis[0]
    # If no opposite phase DWI is available, look for dedicated fieldmaps
    fieldmaps = layout.get_fieldmap(dwi_file)
    if fieldmaps:
        fnames = [list(val.values())[0] for val in fieldmaps]
    opposite_fmaps = []
    for fname in fnames:
        if check_opposite(direction, fname, layout):
            opposite_fmaps.append(fname)
    if len(opposite_fmaps) == 1:
        return opposite_fmaps[0]
    elif len(opposite_fmaps) > 1:
        config.logger.warning(
            """Located more than one opposite phase fieldmap.
            Will use the first one."""
        )
        return opposite_fmaps[0]
    # If no opposite phase fieldmap is available, raise error
    raise NotImplementedError(
        """No opposite phase fieldmap/DWI series found.
    Workflows that do not include PEPOLAR SDC are not currently supported."""
    )


#: Building blocks
OPPOSITE_PHASE_NODE = pe.Node(
    niu.Function(
        **OPPOSITE_PHASE_QUERY_KWARGS, function=locate_opposite_phase
    ),
    name="locate_opposite_phase",
)
