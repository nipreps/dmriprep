from pathlib import Path
from typing import List

from dmriprep import config
from sdcflows.fieldmaps import FieldmapEstimation


def comply_to_filters(
    fmap_estimators: List[FieldmapEstimation], bids_filters: dict
) -> List[FieldmapEstimation]:
    """
    Removes fieldmap estimators that do not comply to BIDS filters.

    Parameters
    ----------
    fmap_estimators : List[FieldmapEstimation]
        A list of detected fieldmap estimators
    bids_filters : dict
        A dictionary of BIDS entities that describe relevant fieldmaps.

    Returns
    -------
    List[FieldmapEstimation]
        A subset of *fmap_estimators*, with only estimators that comply to *bids_filters*
    """
    complied_estimators = fmap_estimators.copy()
    for fmap in fmap_estimators:
        for filename in fmap.paths():
            entities = config.execution.layout.parse_file_entities(filename)
            for key, value in bids_filters.items():
                if (entities.get(key) != value) and (
                    fmap in complied_estimators
                ):
                    complied_estimators.remove(fmap)
    return complied_estimators

def locate_corresponding_fieldmap(fmap_estimators:List[FieldmapEstimation],dwi_file:Path,by="IntendedFor") -> List[Path]:
    """
    Locates fieldmap associated with *dwi_file* from previously detected *fmap_estimators*

    Parameters
    ----------
    fmap_estimators : List[FieldmapEstimation]
        [description]
    dwi_file : Path
        [description]
    by : str, optional
        [description], by default "IntendedFor"

    Returns
    -------
    List[Path]
        [description]
    """

