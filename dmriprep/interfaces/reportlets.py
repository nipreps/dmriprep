"""Interfaces to generate speciality reportlets."""
from nilearn.image import threshold_img, load_img
from niworkflows import NIWORKFLOWS_LOG
from niworkflows.viz.utils import cuts_from_bbox, compose_view
from nipype.interfaces.base import File, isdefined
from nipype.interfaces.mixins import reporting

from ..viz.utils import plot_registration, coolwarm_transparent


class FieldmapReportletInputSpec(reporting.ReportCapableInputSpec):
    reference = File(exists=True, mandatory=True, desc="input reference")
    fieldmap = File(exists=True, mandatory=True, desc="input fieldmap")
    mask = File(exists=True, desc="brain mask")
    out_report = File(
        "report.svg", usedefault=True, desc="filename for the visual report"
    )


class FieldmapReportlet(reporting.ReportCapableInterface):
    """An abstract mixin to registration nipype interfaces."""

    _n_cuts = 7
    input_spec = FieldmapReportletInputSpec
    output_spec = reporting.ReportCapableOutputSpec

    def __init__(self, **kwargs):
        """Instantiate FieldmapReportlet."""
        self._n_cuts = kwargs.pop("n_cuts", self._n_cuts)
        super(FieldmapReportlet, self).__init__(generate_report=True, **kwargs)

    def _run_interface(self, runtime):
        return runtime

    def _generate_report(self):
        """Generate a reportlet."""
        NIWORKFLOWS_LOG.info("Generating visual report")

        refnii = load_img(self.inputs.reference)
        fmapnii = load_img(self.inputs.fieldmap)
        contour_nii = (
            load_img(self.inputs.mask) if isdefined(self.inputs.mask) else None
        )
        mask_nii = threshold_img(refnii, 1e-3)
        cuts = cuts_from_bbox(contour_nii or mask_nii, cuts=self._n_cuts)
        fmapdata = fmapnii.get_fdata()
        vmax = max(fmapdata.max(), abs(fmapdata.min()))

        # Call composer
        compose_view(
            plot_registration(
                refnii,
                "fixed-image",
                estimate_brightness=True,
                cuts=cuts,
                label="reference",
                contour=contour_nii,
                compress=False,
            ),
            plot_registration(
                fmapnii,
                "moving-image",
                estimate_brightness=True,
                cuts=cuts,
                label="fieldmap (Hz)",
                contour=contour_nii,
                compress=False,
                plot_params={
                    "cmap": coolwarm_transparent(),
                    "vmax": vmax,
                    "vmin": -vmax,
                },
            ),
            out_file=self._out_report,
        )
