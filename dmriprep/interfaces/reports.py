# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Interfaces to generate reportlets."""

import os
import time

from collections import Counter
from nipype.interfaces.base import (
    traits, TraitedSpec, BaseInterfaceInputSpec,
    File, Directory, InputMultiObject, Str, isdefined,
    SimpleInterface)
from nipype.interfaces import freesurfer as fs
from niworkflows.utils.bids import BIDS_NAME


SUBJECT_TEMPLATE = """\
\t<ul class="elem-desc">
\t\t<li>Subject ID: {subject_id}</li>
\t\t<li>Structural images: {n_t1s:d} T1-weighted {t2w}</li>
\t\t<li>Diffusion Weighted Images: {n_dwi:d}</li>
{tasks}
\t\t<li>Standard output spaces: {std_spaces}</li>
\t\t<li>Non-standard output spaces: {nstd_spaces}</li>
\t\t<li>FreeSurfer reconstruction: {freesurfer_status}</li>
\t</ul>
"""

DWI_TEMPLATE = """\t\t<h3 class="elem-title">Summary</h3>
\t\t<ul class="elem-desc">
\t\t\t<li>Susceptibility distortion correction: {sdc}</li>
\t\t\t<li>Registration: {registration}</li>
\t\t</ul>
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

        # Add list of tasks with number of runs
        dwi_files = self.inputs.dwi if isdefined(self.inputs.dwi) else []
        dwi_files = [s[0] if isinstance(s, list) else s for s in dwi_files]

        counts = Counter(BIDS_NAME.search(series).groupdict()['task_id'][5:]
                         for series in dwi_files)

        tasks = ''
        if counts:
            header = '\t\t<ul class="elem-desc">'
            footer = '\t\t</ul>'
            lines = ['\t\t\t<li>Task: {task_id} ({n_runs:d} run{s})</li>'.format(
                     task_id=task_id, n_runs=n_runs, s='' if n_runs == 1 else 's')
                     for task_id, n_runs in sorted(counts.items())]
            tasks = '\n'.join([header] + lines + [footer])

        return SUBJECT_TEMPLATE.format(
            subject_id=self.inputs.subject_id,
            n_t1s=len(self.inputs.t1w),
            t2w=t2w_seg,
            n_dwi=len(dwi_files),
            tasks=tasks,
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


class DiffusionSummaryInputSpec(BaseInterfaceInputSpec):
    distortion_correction = traits.Str(desc='Susceptibility distortion correction method',
                                       mandatory=True)
    pe_direction = traits.Enum(None, 'i', 'i-', 'j', 'j-', mandatory=True,
                               desc='Phase-encoding direction detected')
    registration = traits.Enum('FSL', 'FreeSurfer', mandatory=True,
                               desc='Diffusion/anatomical registration method')
    fallback = traits.Bool(desc='Boundary-based registration rejected')
    registration_dof = traits.Enum(6, 9, 12, desc='Registration degrees of freedom',
                                   mandatory=True)


class DiffusionSummary(SummaryInterface):
    input_spec = DiffusionSummaryInputSpec

    def _generate_segment(self):
        dof = self.inputs.registration_dof
        reg = {
            'FSL': [
                'FSL <code>flirt</code> with boundary-based registration'
                ' (BBR) metric - %d dof' % dof,
                'FSL <code>flirt</code> rigid registration - 6 dof'],
            'FreeSurfer': [
                'FreeSurfer <code>bbregister</code> '
                '(boundary-based registration, BBR) - %d dof' % dof,
                'FreeSurfer <code>mri_coreg</code> - %d dof' % dof],
        }[self.inputs.registration][self.inputs.fallback]
        if self.inputs.pe_direction is None:
            pedir = 'MISSING - Assuming Anterior-Posterior'
        else:
            pedir = {'i': 'Left-Right', 'j': 'Anterior-Posterior'}[self.inputs.pe_direction[0]]

        return DWI_TEMPLATE.format(
            pedir=pedir, sdc=self.inputs.distortion_correction, registration=reg)
