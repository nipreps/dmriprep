"""Image tools interfaces."""
import os
import numpy as np
import nibabel as nb
from nipype import logging
from nipype.interfaces import ants
from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import (
    traits, TraitedSpec, BaseInterfaceInputSpec, SimpleInterface, File, isdefined,
    InputMultiObject, OutputMultiObject, CommandLine
)
from ..utils.images import extract_b0, rescale_b0, median, quick_load_images, match_transforms, prune_b0s_from_dwis
from ..utils.vectors import _nonoverlapping_qspace_samples


LOGGER = logging.getLogger('nipype.interface')


class _ExtractB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='dwi file')
    b0_ixs = traits.List(traits.Int, mandatory=True,
                         desc='Index of b0s')


class _ExtractB0OutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='b0 file')


class ExtractB0(SimpleInterface):
    """
    Extract all b=0 volumes from a dwi series.

    Example
    -------
    >>> os.chdir(tmpdir)
    >>> extract_b0 = ExtractB0()
    >>> extract_b0.inputs.in_file = str(data_dir / 'dwi.nii.gz')
    >>> extract_b0.inputs.b0_ixs = [0, 1, 2]
    >>> res = extract_b0.run()  # doctest: +SKIP

    """

    input_spec = _ExtractB0InputSpec
    output_spec = _ExtractB0OutputSpec

    def _run_interface(self, runtime):
        self._results['out_file'] = extract_b0(
            self.inputs.in_file,
            self.inputs.b0_ixs,
            newpath=runtime.cwd)
        return runtime


class _RescaleB0InputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='b0s file')
    mask_file = File(exists=True, mandatory=True, desc='mask file')


class _RescaleB0OutputSpec(TraitedSpec):
    out_ref = File(exists=True, desc='One median b0 file')
    out_b0s = File(exists=True, desc='series of rescaled b0 volumes')


class RescaleB0(SimpleInterface):
    """
    Rescale the b0 volumes to deal with average signal decay over time.

    Example
    -------
    >>> os.chdir(tmpdir)
    >>> rescale_b0 = RescaleB0()
    >>> rescale_b0.inputs.in_file = str(data_dir / 'dwi.nii.gz')
    >>> rescale_b0.inputs.mask_file = str(data_dir / 'dwi_mask.nii.gz')
    >>> res = rescale_b0.run()  # doctest: +SKIP

    """

    input_spec = _RescaleB0InputSpec
    output_spec = _RescaleB0OutputSpec

    def _run_interface(self, runtime):
        self._results['out_b0s'] = rescale_b0(
            self.inputs.in_file,
            self.inputs.mask_file,
            newpath=runtime.cwd
        )
        self._results['out_ref'] = median(
            self._results['out_b0s'],
            newpath=runtime.cwd
        )
        return runtime


class MatchTransformsInputSpec(BaseInterfaceInputSpec):
    b0_indices = traits.List(mandatory=True)
    dwi_files = InputMultiObject(File(exists=True), mandatory=True)
    transforms = InputMultiObject(File(exists=True), mandatory=True)


class MatchTransformsOutputSpec(TraitedSpec):
    transforms = OutputMultiObject(File(exists=True), mandatory=True)


class MatchTransforms(SimpleInterface):
    input_spec = MatchTransformsInputSpec
    output_spec = MatchTransformsOutputSpec

    def _run_interface(self, runtime):
        self._results['transforms'] = match_transforms(self.inputs.dwi_files,
                                                       self.inputs.transforms,
                                                       self.inputs.b0_indices)
        return runtime


class N3BiasFieldCorrection(ants.N4BiasFieldCorrection):
    _cmd = "N3BiasFieldCorrection"


class ImageMathInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, position=3, argstr='%s')
    dimension = traits.Enum(3, 2, 4, usedefault=True, argstr="%d", position=0)
    out_file = File(argstr="%s", genfile=True, position=1)
    operation = traits.Str(argstr="%s", position=2)
    secondary_arg = traits.Str("", argstr="%s")
    secondary_file = File(argstr="%s")


class ImageMathOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ImageMath(CommandLine):
    input_spec = ImageMathInputSpec
    output_spec = ImageMathOutputSpec
    _cmd = 'ImageMath'

    def _gen_filename(self, name):
        if name == 'out_file':
            output = self.inputs.out_file
            if not isdefined(output):
                _, fname, ext = split_filename(self.inputs.in_file)
                output = fname + "_" + self.inputs.operation + ext
            return output
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self._gen_filename('out_file'))
        return outputs


class SignalPredictionInputSpec(BaseInterfaceInputSpec):
    aligned_dwi_files = InputMultiObject(File(exists=True), mandatory=True)
    aligned_vectors = File(exists=True, mandatory=True)
    b0_mask = File(exists=True, mandatory=True)
    b0_median = File(exists=True, mandatory=True)
    bvec_to_predict = traits.Array()
    bval_to_predict = traits.Float()
    minimal_q_distance = traits.Float(2.0, usedefault=True)
    b0_indices = traits.List()


class SignalPredictionOutputSpec(TraitedSpec):
    predicted_image = File(exists=True)


class SignalPrediction(SimpleInterface):
    """
    """
    input_spec = SignalPredictionInputSpec
    output_spec = SignalPredictionOutputSpec

    def _run_interface(self, runtime, model_name='tensor'):
        import warnings
        warnings.filterwarnings("ignore")
        from dipy.core.gradients import gradient_table_from_bvals_bvecs
        pred_vec = self.inputs.bvec_to_predict
        pred_val = self.inputs.bval_to_predict

        # Load the mask image:
        mask_img = nb.load(self.inputs.b0_mask)
        mask_array = mask_img.get_data() > 1e-6

        all_images = prune_b0s_from_dwis(self.inputs.aligned_dwi_files, self.inputs.b0_indices)

        # Load the vectors
        ras_b_mat = np.genfromtxt(self.inputs.aligned_vectors, delimiter='\t')
        all_bvecs = np.row_stack([np.zeros(3), np.delete(ras_b_mat[:, 0:3], self.inputs.b0_indices, axis=0)])
        all_bvals = np.concatenate([np.zeros(1), np.delete(ras_b_mat[:, 3], self.inputs.b0_indices)])

        # Which sample points are too close to the one we want to predict?
        training_mask = _nonoverlapping_qspace_samples(
            pred_val, pred_vec, all_bvals, all_bvecs, self.inputs.minimal_q_distance)
        training_indices = np.flatnonzero(training_mask[1:])
        training_image_paths = [self.inputs.b0_median] + [
            all_images[idx] for idx in training_indices]
        training_bvecs = all_bvecs[training_mask]
        training_bvals = all_bvals[training_mask]
        # print("Training with volumes: {}".format(str(training_indices)))

        # Load training data and fit the model
        training_data = quick_load_images(training_image_paths)

        # Build gradient table object
        training_gtab = gradient_table_from_bvals_bvecs(training_bvals, training_bvecs, b0_threshold=0)

        # Checked shelledness
        if len(np.unique(training_gtab.bvals)) > 2:
            is_shelled = True
        else:
            is_shelled = False

        # Get the vector for the desired coordinate
        prediction_gtab = gradient_table_from_bvals_bvecs(np.array(pred_val)[None], np.array(pred_vec)[None, :],
                                                          b0_threshold=0)

        if is_shelled and model_name == '3dshore':
            from dipy.reconst.shore import ShoreModel
            radial_order = 6
            zeta = 700
            lambdaN = 1e-8
            lambdaL = 1e-8
            estimator_shore = ShoreModel(training_gtab, radial_order=radial_order,
                             zeta=zeta, lambdaN=lambdaN, lambdaL=lambdaL)
            estimator_shore_fit = estimator_shore.fit(training_data, mask=mask_array)
            pred_shore_fit = estimator_shore_fit.predict(prediction_gtab)
            pred_shore_fit_file = os.path.join(runtime.cwd,
                                               "predicted_shore_b%d_%.2f_%.2f_%.2f.nii.gz" %
                                               ((pred_val,) + tuple(np.round(pred_vec, decimals=2))))
            output_data = pred_shore_fit[..., 0]
            nb.Nifti1Image(output_data, mask_img.affine, mask_img.header).to_filename(pred_shore_fit_file)
        elif model_name == 'sfm' and not is_shelled:
            import dipy.reconst.sfm as sfm
            from dipy.data import default_sphere

            estimator_sfm = sfm.SparseFascicleModel(training_gtab, sphere=default_sphere,
                                                    l1_ratio=0.5, alpha=0.001)
            estimator_sfm_fit = estimator_sfm.fit(training_data, mask=mask_array)
            pred_sfm_fit = estimator_sfm_fit.predict(prediction_gtab)[..., 0]
            pred_sfm_fit[~mask_array] = 0
            pred_fit_file = os.path.join(runtime.cwd, "predicted_sfm_b%d_%.2f_%.2f_%.2f.npy" %
            ((pred_val,) + tuple(np.round(pred_vec, decimals=2))))
            np.save(pred_fit_file, pred_sfm_fit)
            pred_fit_file = os.path.join(runtime.cwd, "predicted_sfm_b%d_%.2f_%.2f_%.2f.nii.gz" %
            ((pred_val,) + tuple(np.round(pred_vec, decimals=2))))
            nb.Nifti1Image(pred_sfm_fit, mask_img.affine, mask_img.header).to_filename(pred_fit_file)
        else:
            from dipy.reconst.dti import TensorModel
            estimator_ten = TensorModel(training_gtab)
            estimator_ten_fit = estimator_ten.fit(training_data, mask=mask_array)
            pred_ten_fit = estimator_ten_fit.predict(prediction_gtab)[..., 0]
            pred_ten_fit[~mask_array] = 0
            pred_fit_file = os.path.join(runtime.cwd, "predicted_ten_b%d_%.2f_%.2f_%.2f.npy" %
            ((pred_val,) + tuple(np.round(pred_vec, decimals=2))))
            np.save(pred_fit_file, pred_ten_fit)
            pred_fit_file = os.path.join(runtime.cwd, "predicted_ten_b%d_%.2f_%.2f_%.2f.nii.gz" %
                                         ((pred_val,) + tuple(np.round(pred_vec, decimals=2))))
            nb.Nifti1Image(pred_ten_fit, mask_img.affine, mask_img.header).to_filename(pred_fit_file)

        self._results['predicted_image'] = pred_fit_file

        return runtime


class CalculateCNRInputSpec(BaseInterfaceInputSpec):
    emc_warped_images = InputMultiObject(File(exists=True))
    predicted_images = InputMultiObject(File(exists=True))
    mask_image = File(exists=True)


class CalculateCNROutputSpec(TraitedSpec):
    cnr_image = File(exists=True)


class CalculateCNR(SimpleInterface):
    input_spec = CalculateCNRInputSpec
    output_spec = CalculateCNROutputSpec

    def _run_interface(self, runtime):
        cnr_file = os.path.join(runtime.cwd, "emc_CNR.nii.gz")
        model_images = quick_load_images(self.inputs.predicted_images)
        observed_images = quick_load_images(self.inputs.emc_warped_images)
        mask_image = nb.load(self.inputs.mask_image)
        mask = mask_image.get_data() > 1e-6
        signal_vals = model_images[mask]
        b0 = signal_vals[:, 0][:, np.newaxis]
        signal_vals = signal_vals / b0
        signal_var = np.var(signal_vals, 1)
        observed_vals = observed_images[mask] / b0
        noise_var = np.var(signal_vals - observed_vals, 1)
        snr = np.nan_to_num(signal_var / noise_var)
        out_mat = np.zeros(mask_image.shape)
        out_mat[mask] = snr
        nb.Nifti1Image(out_mat, mask_image.affine,
                       header=mask_image.header).to_filename(cnr_file)
        self._results['cnr_image'] = cnr_file
        return runtime


class ReorderOutputsInputSpec(BaseInterfaceInputSpec):
    b0_indices = traits.List(mandatory=True)
    b0_median = File(exists=True, mandatory=True)
    warped_b0_images = InputMultiObject(File(exists=True), mandatory=True)
    warped_dwi_images = InputMultiObject(File(exists=True), mandatory=True)
    initial_transforms = InputMultiObject(File(exists=True), mandatory=True)
    model_based_transforms = InputMultiObject(traits.List(), mandatory=True)
    model_predicted_images = InputMultiObject(File(exists=True), mandatory=True)


class ReorderOutputsOutputSpec(TraitedSpec):
    full_transforms = OutputMultiObject(traits.List())
    full_predicted_dwi_series = OutputMultiObject(File(exists=True))
    emc_warped_images = OutputMultiObject(File(exists=True))


class ReorderOutputs(SimpleInterface):
    input_spec = ReorderOutputsInputSpec
    output_spec = ReorderOutputsOutputSpec

    def _run_interface(self, runtime):
        full_transforms = []
        full_predicted_dwi_series = []
        full_warped_images = []
        warped_b0_images = self.inputs.warped_b0_images[::-1]
        warped_dwi_images = self.inputs.warped_dwi_images[::-1]
        model_transforms = self.inputs.model_based_transforms[::-1]
        model_images = self.inputs.model_predicted_images[::-1]
        b0_transforms = [self.inputs.initial_transforms[idx] for idx in
                         self.inputs.b0_indices][::-1]
        num_dwis = len(self.inputs.initial_transforms)

        for imagenum in range(num_dwis):
            if imagenum in self.inputs.b0_indices:
                full_predicted_dwi_series.append(self.inputs.b0_median)
                full_transforms.append(b0_transforms.pop())
                full_warped_images.append(warped_b0_images.pop())
            else:
                full_transforms.append(model_transforms.pop())
                full_predicted_dwi_series.append(model_images.pop())
                full_warped_images.append(warped_dwi_images.pop())

        if not len(model_transforms) == len(b0_transforms) == len(model_images) == 0:
            raise Exception("Unable to recombine images and transforms")

        self._results['emc_warped_images'] = full_warped_images
        self._results['full_transforms'] = full_transforms
        self._results['full_predicted_dwi_series'] = full_predicted_dwi_series

        return runtime
