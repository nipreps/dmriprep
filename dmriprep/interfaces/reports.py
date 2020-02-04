# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Interfaces to generate reportlets."""

import os
import time
import pandas as pd
from nipype.interfaces.base import (
    traits, TraitedSpec, BaseInterfaceInputSpec,
    File, Directory, InputMultiObject, Str, isdefined,
    SimpleInterface)
from nipype.interfaces import freesurfer as fs
from ..utils.viz import _iteration_summary_plot, before_after_images

SUBJECT_TEMPLATE = """\
\t<ul class="elem-desc">
\t\t<li>Subject ID: {subject_id}</li>
\t\t<li>Structural images: {n_t1s:d} T1-weighted {t2w}</li>
\t\t<li>Diffusion Weighted Images: {n_dwi:d}</li>
\t\t<li>Standard output spaces: {std_spaces}</li>
\t\t<li>Non-standard output spaces: {nstd_spaces}</li>
\t\t<li>FreeSurfer reconstruction: {freesurfer_status}</li>
\t</ul>
"""

ABOUT_TEMPLATE = """\t<ul>
\t\t<li>dMRIPrep version: {version}</li>
\t\t<li>dMRIPrep command: <code>{command}</code></li>
\t\t<li>Date preprocessed: {date}</li>
\t</ul>
</div>
"""


class SummaryOutputSpec(TraitedSpec):
    out_report = File(exists=True, desc='HTML segment containing summary')


class SummaryInterface(SimpleInterface):
    output_spec = SummaryOutputSpec

    def _run_interface(self, runtime):
        segment = self._generate_segment()
        fname = os.path.join(runtime.cwd, 'report.html')
        with open(fname, 'w') as fobj:
            fobj.write(segment)
        self._results['out_report'] = fname
        return runtime

    def _generate_segment(self):
        raise NotImplementedError


class SubjectSummaryInputSpec(BaseInterfaceInputSpec):
    t1w = InputMultiObject(File(exists=True), desc='T1w structural images')
    t2w = InputMultiObject(File(exists=True), desc='T2w structural images')
    subjects_dir = Directory(desc='FreeSurfer subjects directory')
    subject_id = Str(desc='Subject ID')
    dwi = InputMultiObject(traits.Either(
        File(exists=True), traits.List(File(exists=True))),
        desc='DWI files')
    std_spaces = traits.List(Str, desc='list of standard spaces')
    nstd_spaces = traits.List(Str, desc='list of non-standard spaces')


class SubjectSummaryOutputSpec(SummaryOutputSpec):
    # This exists to ensure that the summary is run prior to the first ReconAll
    # call, allowing a determination whether there is a pre-existing directory
    subject_id = Str(desc='FreeSurfer subject ID')


class SubjectSummary(SummaryInterface):
    input_spec = SubjectSummaryInputSpec
    output_spec = SubjectSummaryOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.subject_id):
            self._results['subject_id'] = self.inputs.subject_id
        return super(SubjectSummary, self)._run_interface(runtime)

    def _generate_segment(self):
        if not isdefined(self.inputs.subjects_dir):
            freesurfer_status = 'Not run'
        else:
            recon = fs.ReconAll(subjects_dir=self.inputs.subjects_dir,
                                subject_id=self.inputs.subject_id,
                                T1_files=self.inputs.t1w,
                                flags='-noskullstrip')
            if recon.cmdline.startswith('echo'):
                freesurfer_status = 'Pre-existing directory'
            else:
                freesurfer_status = 'Run by dMRIPrep'

        t2w_seg = ''
        if self.inputs.t2w:
            t2w_seg = '(+ {:d} T2-weighted)'.format(len(self.inputs.t2w))

        dwi_files = self.inputs.dwi if isdefined(self.inputs.dwi) else []
        dwi_files = [s[0] if isinstance(s, list) else s for s in dwi_files]

        return SUBJECT_TEMPLATE.format(
            subject_id=self.inputs.subject_id,
            n_t1s=len(self.inputs.t1w),
            t2w=t2w_seg,
            n_dwi=len(dwi_files),
            std_spaces=', '.join(self.inputs.std_spaces),
            nstd_spaces=', '.join(self.inputs.nstd_spaces),
            freesurfer_status=freesurfer_status)


class AboutSummaryInputSpec(BaseInterfaceInputSpec):
    version = Str(desc='dMRIPrep version')
    command = Str(desc='dMRIPrep command')
    # Date not included - update timestamp only if version or command changes


class AboutSummary(SummaryInterface):
    input_spec = AboutSummaryInputSpec

    def _generate_segment(self):
        return ABOUT_TEMPLATE.format(version=self.inputs.version,
                                     command=self.inputs.command,
                                     date=time.strftime("%Y-%m-%d %H:%M:%S %z"))


class IterationSummaryInputSpec(BaseInterfaceInputSpec):
    collected_motion_files = InputMultiObject(File(exists=True))


class IterationSummaryOutputSpec(TraitedSpec):
    iteration_summary_file = File(exists=True)
    plot_file = File(exists=True)


class IterationSummary(SummaryInterface):
    input_spec = IterationSummaryInputSpec
    output_spec = IterationSummaryOutputSpec

    def _run_interface(self, runtime):
        motion_files = self.inputs.collected_motion_files
        output_fname = os.path.join(runtime.cwd, "iteration_summary.csv")
        fig_output_fname = os.path.join(runtime.cwd, "iterdiffs.svg")
        if not isdefined(motion_files):
            return runtime

        all_iters = []
        for fnum, fname in enumerate(motion_files):
            df = pd.read_csv(fname)
            df['iter_num'] = fnum
            path_parts = fname.split(os.sep)
            itername = '' if 'iter' not in path_parts[-3] else path_parts[-3]
            df['iter_name'] = itername
            all_iters.append(df)
        combined = pd.concat(all_iters, axis=0, ignore_index=True)

        combined.to_csv(output_fname, index=False)
        self._results['iteration_summary_file'] = output_fname

        # Create a figure for the report
        _iteration_summary_plot(combined, fig_output_fname)
        self._results['plot_file'] = fig_output_fname

        return runtime


class EMCReportInputSpec(BaseInterfaceInputSpec):
    iteration_summary = File(exists=True)
    registered_images = InputMultiObject(File(exists=True))
    original_images = InputMultiObject(File(exists=True))
    model_predicted_images = InputMultiObject(File(exists=True))


class EMCReportOutputSpec(SummaryOutputSpec):
    plot_file = File(exists=True)


class EMCReport(SummaryInterface):
    input_spec = EMCReportInputSpec
    output_spec = EMCReportOutputSpec

    def _run_interface(self, runtime):
        import imageio
        images = []
        for imagenum, (orig_file, aligned_file, model_file) in enumerate(zip(
                self.inputs.original_images, self.inputs.registered_images,
                self.inputs.model_predicted_images)):

            images.extend(before_after_images(orig_file, aligned_file, model_file, imagenum))

        out_file = os.path.join(runtime.cwd, "emc_reg.gif")
        imageio.mimsave(out_file, images, fps=1)
        self._results['plot_file'] = out_file
        return runtime
