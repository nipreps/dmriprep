import os
import os.path as op

from nipype.interfaces import fsl
from nipype.interfaces.base import isdefined


class ExtendedEddyOutputSpec(fsl.epi.EddyOutputSpec):
    from nipype.interfaces.base import File

    shell_PE_translation_parameters = File(
        exists=True,
        desc="the translation along the PE-direction between the different shells",
    )
    outlier_map = File(
        exists=True,
        desc="All numbers are either 0, meaning that scan-slice "
        "is not an outliers, or 1 meaning that it is.",
    )
    outlier_n_stdev_map = File(
        exists=True,
        desc="how many standard deviations off the mean difference "
        "between observation and prediction is.",
    )
    outlier_n_sqr_stdev_map = File(
        exists=True,
        desc="how many standard deviations off the square root of the "
        "mean squared difference between observation and prediction is.",
    )
    outlier_free_data = File(
        exists=True,
        desc=" the original data given by --imain not corrected for "
        "susceptibility or EC-induced distortions or subject movement, but with "
        "outlier slices replaced by the Gaussian Process predictions.",
    )


class ExtendedEddy(fsl.Eddy):
    output_spec = ExtendedEddyOutputSpec
    _num_threads = 1

    def __init__(self, **inputs):
        super(fsl.Eddy, self).__init__(**inputs)
        self.inputs.on_trait_change(self._num_threads_update, "num_threads")
        if not isdefined(self.inputs.num_threads):
            self.inputs.num_threads = self._num_threads
        else:
            self._num_threads_update()
        self.inputs.on_trait_change(self._use_cuda, "use_cuda")
        if isdefined(self.inputs.use_cuda):
            self._use_cuda()

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_corrected"] = os.path.abspath("%s.nii.gz" % self.inputs.out_base)
        outputs["out_parameter"] = os.path.abspath(
            "%s.eddy_parameters" % self.inputs.out_base
        )

        # File generation might depend on the version of EDDY
        out_rotated_bvecs = os.path.abspath(
            "%s.eddy_rotated_bvecs" % self.inputs.out_base
        )
        out_movement_rms = os.path.abspath(
            "%s.eddy_movement_rms" % self.inputs.out_base
        )
        out_restricted_movement_rms = os.path.abspath(
            "%s.eddy_restricted_movement_rms" % self.inputs.out_base
        )
        out_shell_alignment_parameters = os.path.abspath(
            "%s.eddy_post_eddy_shell_alignment_parameters" % self.inputs.out_base
        )
        shell_PE_translation_parameters = op.abspath(
            "%s.eddy_post_eddy_shell_PE_translation_parameters" % self.inputs.out_base
        )
        out_outlier_report = os.path.abspath(
            "%s.eddy_outlier_report" % self.inputs.out_base
        )
        outlier_map = op.abspath("%s.eddy_outlier_map" % self.inputs.out_base)
        outlier_n_stdev_map = op.abspath(
            "%s.eddy_outlier_n_stdev_map" % self.inputs.out_base
        )
        outlier_n_sqr_stdev_map = op.abspath(
            "%s.eddy_outlier_n_sqr_stdev_map" % self.inputs.out_base
        )
        outlier_free_data = op.abspath(
            "%s.eddy_outlier_free_data.nii.gz" % self.inputs.out_base
        )

        if isdefined(self.inputs.cnr_maps) and self.inputs.cnr_maps:
            out_cnr_maps = os.path.abspath(
                "%s.eddy_cnr_maps.nii.gz" % self.inputs.out_base
            )
            if os.path.exists(out_cnr_maps):
                outputs["out_cnr_maps"] = out_cnr_maps
        if isdefined(self.inputs.residuals) and self.inputs.residuals:
            out_residuals = os.path.abspath(
                "%s.eddy_residuals.nii.gz" % self.inputs.out_base
            )
            if os.path.exists(out_residuals):
                outputs["out_residuals"] = out_residuals

        if os.path.exists(out_rotated_bvecs):
            outputs["out_rotated_bvecs"] = out_rotated_bvecs
        if os.path.exists(out_movement_rms):
            outputs["out_movement_rms"] = out_movement_rms
        if os.path.exists(out_restricted_movement_rms):
            outputs["out_restricted_movement_rms"] = out_restricted_movement_rms
        if os.path.exists(out_shell_alignment_parameters):
            outputs["out_shell_alignment_parameters"] = out_shell_alignment_parameters
        if os.path.exists(out_outlier_report):
            outputs["out_outlier_report"] = out_outlier_report
        if os.path.exists(outlier_free_data):
            outputs["outlier_free_data"] = outlier_free_data
        if op.exists(shell_PE_translation_parameters):
            outputs["shell_PE_translation_parameters"] = shell_PE_translation_parameters
        if op.exists(outlier_map):
            outputs["outlier_map"] = outlier_map
        if op.exists(outlier_n_stdev_map):
            outputs["outlier_n_stdev_map"] = outlier_n_stdev_map
        if op.exists(outlier_n_sqr_stdev_map):
            outputs["outlier_n_sqr_stdev_map"] = outlier_n_sqr_stdev_map

        return outputs
