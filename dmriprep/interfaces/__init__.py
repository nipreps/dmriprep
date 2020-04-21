# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Custom Nipype interfaces for dMRIPrep."""
from nipype.interfaces.base import OutputMultiObject, SimpleInterface
from niworkflows.interfaces.bids import (
    DerivativesDataSink as _DDS,
    _BIDSDataGrabberOutputSpec,
    _BIDSDataGrabberInputSpec,
    LOGGER as _LOGGER,
)


class DerivativesDataSink(_DDS):
    """A patched DataSink."""

    out_path_base = "dmriprep"


class BIDSDataGrabberOutputSpec(_BIDSDataGrabberOutputSpec):
    dwi = OutputMultiObject(desc="output DWI images")


class BIDSDataGrabber(SimpleInterface):
    input_spec = _BIDSDataGrabberInputSpec
    output_spec = BIDSDataGrabberOutputSpec
    _require_dwis = True

    def __init__(self, *args, **kwargs):
        anat_only = kwargs.pop("anat_only", False)
        super(BIDSDataGrabber, self).__init__(*args, **kwargs)
        if anat_only is not None:
            self._require_dwis = not anat_only

    def _run_interface(self, runtime):
        bids_dict = self.inputs.subject_data

        self._results["out_dict"] = bids_dict
        self._results.update(bids_dict)

        if not bids_dict["t1w"]:
            raise FileNotFoundError(
                "No T1w images found for subject sub-{}".format(self.inputs.subject_id)
            )

        if self._require_dwis and not bids_dict["dwi"]:
            raise FileNotFoundError(
                "No diffusion weighted images found for subject sub-{}".format(
                    self.inputs.subject_id
                )
            )

        for imtype in ["dwi", "t2w", "flair", "fmap", "roi"]:
            if not bids_dict[imtype]:
                _LOGGER.warning(
                    'No "%s" images found for sub-%s', imtype, self.inputs.subject_id
                )

        return runtime
