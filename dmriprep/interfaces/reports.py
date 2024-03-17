# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright 2021 The NiPreps Developers <nipreps@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#
"""Interfaces to generate reportlets."""

import logging
import os
import re
import time

from nipype.interfaces import freesurfer as fs
from nipype.interfaces.base import (
    BaseInterfaceInputSpec,
    Directory,
    File,
    InputMultiObject,
    SimpleInterface,
    Str,
    TraitedSpec,
    isdefined,
    traits,
)

LOGGER = logging.getLogger("nipype.interface")

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

DWI_TEMPLATE = """\
\t\t<details open>
\t\t<summary>Summary</summary>
\t\t<ul class="elem-desc">
\t\t\t<li>Original orientation: {ornt}</li>
\t\t\t<li>Phase-encoding (PE) direction: {pedir}</li>
\t\t\t<li>Susceptibility distortion correction: {sdc}</li>
\t\t\t<li>Registration: {registration}</li>
\t\t</ul>
\t\t</details>
\t\t<details>
\t\t\t<summary>Confounds collected</summary><br />
\t\t\t<p>{confounds}.</p>
\t\t</details>
"""

ABOUT_TEMPLATE = """\t<ul>
\t\t<li>dMRIPrep version: {version}</li>
\t\t<li>dMRIPrep command: <code>{command}</code></li>
\t\t<li>Date preprocessed: {date}</li>
\t</ul>
</div>
"""


class SummaryOutputSpec(TraitedSpec):
    out_report = File(exists=True, desc="HTML segment containing summary")


class SummaryInterface(SimpleInterface):
    output_spec = SummaryOutputSpec

    def _run_interface(self, runtime):
        segment = self._generate_segment()
        fname = os.path.join(runtime.cwd, "report.html")
        with open(fname, "w") as fobj:
            fobj.write(segment)
        self._results["out_report"] = fname
        return runtime

    def _generate_segment(self):
        raise NotImplementedError


class SubjectSummaryInputSpec(BaseInterfaceInputSpec):
    t1w = InputMultiObject(File(exists=True), desc="T1w structural images")
    t2w = InputMultiObject(File(exists=True), desc="T2w structural images")
    subjects_dir = Directory(desc="FreeSurfer subjects directory")
    subject_id = Str(desc="Subject ID")
    dwi = InputMultiObject(
        traits.Either(File(exists=True), traits.List(File(exists=True))),
        desc="DWI files",
    )
    std_spaces = traits.List(Str, desc="list of standard spaces")
    nstd_spaces = traits.List(Str, desc="list of non-standard spaces")


class SubjectSummaryOutputSpec(SummaryOutputSpec):
    # This exists to ensure that the summary is run prior to the first ReconAll
    # call, allowing a determination whether there is a pre-existing directory
    subject_id = Str(desc="FreeSurfer subject ID")


class SubjectSummary(SummaryInterface):
    input_spec = SubjectSummaryInputSpec
    output_spec = SubjectSummaryOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.subject_id):
            self._results["subject_id"] = self.inputs.subject_id
        return super(SubjectSummary, self)._run_interface(runtime)

    def _generate_segment(self):
        if not isdefined(self.inputs.subjects_dir):
            freesurfer_status = "Not run"
        else:
            recon = fs.ReconAll(
                subjects_dir=self.inputs.subjects_dir,
                subject_id=self.inputs.subject_id,
                T1_files=self.inputs.t1w,
                flags="-noskullstrip",
            )
            if recon.cmdline.startswith("echo"):
                freesurfer_status = "Pre-existing directory"
            else:
                freesurfer_status = "Run by dMRIPrep"

        t2w_seg = ""
        if self.inputs.t2w:
            t2w_seg = "(+ {:d} T2-weighted)".format(len(self.inputs.t2w))

        dwi_files = self.inputs.dwi if isdefined(self.inputs.dwi) else []
        dwi_files = [s[0] if isinstance(s, list) else s for s in dwi_files]

        return SUBJECT_TEMPLATE.format(
            subject_id=self.inputs.subject_id,
            n_t1s=len(self.inputs.t1w),
            t2w=t2w_seg,
            n_dwi=len(dwi_files),
            std_spaces=", ".join(self.inputs.std_spaces),
            nstd_spaces=", ".join(self.inputs.nstd_spaces),
            freesurfer_status=freesurfer_status,
        )


class DwiSummaryInputSpec(BaseInterfaceInputSpec):
    distortion_correction = traits.Str(
        desc="Susceptibility distortion correction method", mandatory=True
    )
    pe_direction = traits.Enum(
        None,
        "i",
        "i-",
        "j",
        "j-",
        "k",
        "k-",
        mandatory=True,
        desc="Phase-encoding direction detected",
    )
    registration = traits.Enum(
        "FSL",
        "FreeSurfer",
        mandatory=True,
        desc="Diffusion/anatomical registration method",
    )
    fallback = traits.Bool(desc="Boundary-based registration rejected")
    registration_dof = traits.Enum(
        6, 9, 12, desc="Registration degrees of freedom", mandatory=True
    )
    registration_init = traits.Enum(
        "register",
        "header",
        mandatory=True,
        desc='Whether to initialize registration with the "header"'
        ' or by centering the volumes ("register")',
    )
    confounds_file = File(exists=True, desc="Confounds file")
    orientation = traits.Str(
        mandatory=True, desc="Orientation of the voxel axes"
    )


class FunctionalSummary(SummaryInterface):
    input_spec = DwiSummaryInputSpec

    def _generate_segment(self):
        dof = self.inputs.registration_dof
        reg = {
            "FSL": [
                "FSL <code>flirt</code> with boundary-based registration"
                " (BBR) metric - %d dof" % dof,
                "FSL <code>flirt</code> rigid registration - 6 dof",
            ],
            "FreeSurfer": [
                "FreeSurfer <code>bbregister</code> "
                "(boundary-based registration, BBR) - %d dof" % dof,
                "FreeSurfer <code>mri_coreg</code> - %d dof" % dof,
            ],
        }[self.inputs.registration][self.inputs.fallback]

        pedir = get_world_pedir(
            self.inputs.orientation, self.inputs.pe_direction
        )

        if isdefined(self.inputs.confounds_file):
            with open(self.inputs.confounds_file) as cfh:
                conflist = cfh.readline().strip("\n").strip()

        return DWI_TEMPLATE.format(
            pedir=pedir,
            sdc=self.inputs.distortion_correction,
            registration=reg,
            confounds=re.sub(r"[\t ]+", ", ", conflist),
            ornt=self.inputs.orientation,
        )


class AboutSummaryInputSpec(BaseInterfaceInputSpec):
    version = Str(desc="dMRIPrep version")
    command = Str(desc="dMRIPrep command")
    # Date not included - update timestamp only if version or command changes


class AboutSummary(SummaryInterface):
    input_spec = AboutSummaryInputSpec

    def _generate_segment(self):
        return ABOUT_TEMPLATE.format(
            version=self.inputs.version,
            command=self.inputs.command,
            date=time.strftime("%Y-%m-%d %H:%M:%S %z"),
        )


def get_world_pedir(ornt, pe_direction):
    """Return world direction of phase encoding"""
    axes = (
        ("Right", "Left"),
        ("Anterior", "Posterior"),
        ("Superior", "Inferior"),
    )
    ax_idcs = {"i": 0, "j": 1, "k": 2}

    if pe_direction is not None:
        axcode = ornt[ax_idcs[pe_direction[0]]]
        inv = pe_direction[1:] == "-"

        for ax in axes:
            for flip in (ax, ax[::-1]):
                if flip[not inv].startswith(axcode):
                    return "-".join(flip)
    LOGGER.warning(
        "Cannot determine world direction of phase encoding. "
        f"Orientation: {ornt}; PE dir: {pe_direction}"
    )
    return "Could not be determined - assuming Anterior-Posterior"
