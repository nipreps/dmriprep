from nipype import logging
from nipype.interfaces.base import (
    BaseInterfaceInputSpec,
    OutputMultiObject,
    SimpleInterface,
    Str,
    TraitedSpec,
    traits,
)

LOGGER = logging.getLogger("nipype.interface")


class _BIDSDataGrabberInputSpec(BaseInterfaceInputSpec):
    subject_data = traits.Dict(Str, traits.Any)
    subject_id = Str()


class _BIDSDataGrabberOutputSpec(TraitedSpec):
    out_dict = traits.Dict(desc="output data structure")
    fmap = OutputMultiObject(desc="output fieldmaps")
    dwi = OutputMultiObject(desc="output DWI images")
    t1w = OutputMultiObject(desc="output T1w images")
    roi = OutputMultiObject(desc="output ROI images")
    t2w = OutputMultiObject(desc="output T2w images")
    flair = OutputMultiObject(desc="output FLAIR images")


class BIDSDataGrabber(SimpleInterface):
    """
    Collect files from a BIDS directory structure.

    .. testsetup::

        >>> data_dir_canary()

    >>> bids_src = BIDSDataGrabber(anat_only=False)
    >>> bids_src.inputs.subject_data = bids_collect_data(
    ...     str(datadir / 'ds114'), '01', bids_validate=False)[0]
    >>> bids_src.inputs.subject_id = '01'
    >>> res = bids_src.run()
    >>> res.outputs.t1w  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    ['.../ds114/sub-01/ses-retest/anat/sub-01_ses-retest_T1w.nii.gz',
     '.../ds114/sub-01/ses-test/anat/sub-01_ses-test_T1w.nii.gz']

    """

    input_spec = _BIDSDataGrabberInputSpec
    output_spec = _BIDSDataGrabberOutputSpec
    _require_dwis = True

    def __init__(self, *args, **kwargs):
        anat_only = kwargs.pop("anat_only")
        anat_derivatives = kwargs.pop("anat_derivatives", None)
        super(BIDSDataGrabber, self).__init__(*args, **kwargs)
        if anat_only is not None:
            self._require_dwis = not anat_only
        self._require_t1w = anat_derivatives is None

    def _run_interface(self, runtime):
        bids_dict = self.inputs.subject_data

        self._results["out_dict"] = bids_dict
        self._results.update(bids_dict)

        if self._require_t1w and not bids_dict["t1w"]:
            raise FileNotFoundError(
                "No T1w images found for subject sub-{}".format(
                    self.inputs.subject_id
                )
            )

        if self._require_dwis and not bids_dict["dwi"]:
            raise FileNotFoundError(
                "No functional images found for subject sub-{}".format(
                    self.inputs.subject_id
                )
            )

        for imtype in ["dwi", "t2w", "flair", "fmap", "roi"]:
            if not bids_dict[imtype]:
                LOGGER.info(
                    'No "%s" images found for sub-%s',
                    imtype,
                    self.inputs.subject_id,
                )

        return runtime
