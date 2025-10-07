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
"""
The workflow builder factory method.

All the checks and the construction of the workflow are done
inside this function that has pickleable inputs and output
dictionary (``retval``) to allow isolation using a
``multiprocessing.Process`` that allows dmriprep to enforce
a hard-limited memory-scope.

"""


def build_workflow(config_file, retval):
    """Create the Nipype Workflow that supports the whole execution graph."""
    from niworkflows.utils.bids import collect_participants, check_pipeline_version
    from niworkflows.reports import generate_reports
    from .. import config
    from ..utils.misc import check_deps
    from ..workflows.base import init_dmriprep_wf

    config.load(config_file)
    build_log = config.loggers.workflow

    output_dir = config.execution.output_dir
    version = config.environment.version

    retval["return_code"] = 1
    retval["workflow"] = None

    # warn if older results exist: check for dataset_description.json in output folder
    msg = check_pipeline_version(
        version, output_dir / "dmriprep" / "dataset_description.json"
    )
    if msg is not None:
        build_log.warning(msg)

    # Please note this is the input folder's dataset_description.json
    dset_desc_path = config.execution.bids_dir / "dataset_description.json"
    if dset_desc_path.exists():
        from hashlib import sha256

        desc_content = dset_desc_path.read_bytes()
        config.execution.bids_description_hash = sha256(desc_content).hexdigest()

    # First check that bids_dir looks like a BIDS folder
    subject_list = collect_participants(
        config.execution.layout, participant_label=config.execution.participant_label
    )

    # Called with reports only
    if config.execution.reports_only:
        from pkg_resources import resource_filename as pkgrf

        build_log.log(
            25, f"Running --reports-only on participants {', '.join(subject_list)}",
        )
        retval["return_code"] = generate_reports(
            subject_list,
            config.execution.output_dir,
            config.execution.run_uuid,
            config=pkgrf("dmriprep", "config/reports-spec.yml"),
            packagename="dmriprep",
        )
        return retval

    # Build main workflow
    INIT_MSG = f"""
    Running dMRIPrep version {config.environment.version}:
      * BIDS dataset path: {config.execution.bids_dir}.
      * Participant list: {subject_list}.
      * Run identifier: {config.execution.run_uuid}.
      * Output spaces: {config.execution.output_spaces}.
    """
    build_log.log(25, INIT_MSG)

    retval["workflow"] = init_dmriprep_wf()

    # Check workflow for missing commands
    missing = check_deps(retval["workflow"])
    if missing:
        deps_list = "\n".join([f"\t* {cmd} (Interface: {iface})" for iface, cmd in missing])
        build_log.critical(f"Cannot run dMRIPrep. Missing dependencies:\n{deps_list}")
        retval["return_code"] = 127  # 127 == command not found.
        return retval

    config.to_filename(config_file)
    build_log.info(
        f"dMRIPrep workflow graph with {len(retval['workflow']._get_all_nodes())} nodes built successfully."
    )
    retval["return_code"] = 0
    return retval


def build_boilerplate(config_file, workflow):
    """Write boilerplate in an isolated process."""
    from .. import config

    config.load(config_file)
    logs_path = config.execution.output_dir / "dmriprep" / "logs"
    boilerplate = workflow.visit_desc()
    citation_files = {
        ext: logs_path / (f"CITATION.{[ext for ext in ('bib', 'tex', 'md', 'html')]}")
    }

    if boilerplate:
        # To please git-annex users and also to guarantee consistency
        # among different renderings of the same file, first remove any
        # existing one
        for citation_file in citation_files.values():
            try:
                citation_file.unlink()
            except FileNotFoundError:
                pass

    citation_files["md"].write_text(boilerplate)

    if not config.execution.md_only_boilerplate and citation_files["md"].exists():
        from subprocess import check_call, CalledProcessError, TimeoutExpired
        from pkg_resources import resource_filename as pkgrf
        from shutil import copyfile

        # Generate HTML file resolving citations
        cmd = [
            "pandoc",
            "-s",
            "--bibliography",
            pkgrf("dmriprep", "data/boilerplate.bib"),
            "--citeproc",
            "--metadata",
            'pagetitle="dMRIPrep citation boilerplate"',
            str(citation_files["md"]),
            "-o",
            str(citation_files["html"]),
        ]

        config.loggers.cli.info(
            "Generating an HTML version of the citation boilerplate..."
        )
        try:
            check_call(cmd, timeout=10)
        except (FileNotFoundError, CalledProcessError, TimeoutExpired):
            config.loggers.cli.warning(
                f"Could not generate CITATION.html file:\n{' '.join(cmd)}"
            )

        # Generate LaTex file resolving citations
        cmd = [
            "pandoc",
            "-s",
            "--bibliography",
            pkgrf("dmriprep", "data/boilerplate.bib"),
            "--natbib",
            str(citation_files["md"]),
            "-o",
            str(citation_files["tex"]),
        ]
        config.loggers.cli.info(
            "Generating a LaTeX version of the citation boilerplate..."
        )
        try:
            check_call(cmd, timeout=10)
        except (FileNotFoundError, CalledProcessError, TimeoutExpired):
            config.loggers.cli.warning(
                f"Could not generate CITATION.tex file:\n{' '.join(cmd)}"
            )
        else:
            copyfile(pkgrf("dmriprep", "data/boilerplate.bib"), citation_files["bib"])
