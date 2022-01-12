from pathlib import Path
from typing import List

from dmriprep import config
from sdcflows.fieldmaps import FieldmapEstimation

from bids import BIDSLayout


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


def locate_corresponding_fieldmap(
    fmap_estimators: List[FieldmapEstimation], dwi_file: Path, by="IntendedFor"
) -> List[Path]:
    """
    Locates fieldmap associated with *dwi_file* from previously detected *fmap_estimators*

    Parameters
    ----------
    fmap_estimators : List[FieldmapEstimation]
        A list of detected fieldmap estimators
    dwi_file : Path
        Path to DWI series to be processed
    by : str, optional
        Field to query fieldmap's metadata by, by default "IntendedFor"

    Returns
    -------
    List[Path]
        List of paths to fieldmaps related to *dwi_file*
    """
    subject = config.execution.layout.parse_file_entities(dwi_file).get(
        "subject"
    )
    target = str(
        dwi_file.relative_to(config.execution.bids_dir / f"sub-{subject}")
    )
    corresponding_fmaps = fmap_estimators.copy()
    for fmap in fmap_estimators:
        for source in fmap.sources:
            if (target not in source.metadata.get(by)) and (
                fmap in corresponding_fmaps
            ):
                corresponding_fmaps.remove(fmap)
    return corresponding_fmaps


def locate_corresponding_json(layout: BIDSLayout, image_file: Path) -> str:
    """
    Locates json metadata file corresponding to *image_file*.

    Parameters
    ----------
    layout : BIDSLayout
        BIDS layout describing dataset to be queried.
    image_file : Path
        Path to image file to locate its corresponding json metadata.

    Returns
    -------
    str
        Path to json metadata file corresponding to *image_file*.
    """
    entities = layout.parse_file_entities(image_file)
    entities["extension"] = "json"
    return layout.get(**entities)[0].path
