#!/usr/bin/env python
"""dMRI preprocessing workflow."""
from .. import config


def main():
    """Entry point."""
    import os
    import sys
    import gc
    from multiprocessing import Process, Manager
    from .parser import parse_args
    from ..utils.bids import write_derivative_description

    parse_args()

    popylar = None
    if not config.execution.notrack:
        import popylar
        from ..__about__ import __ga_id__

        config.loggers.cli.info(
            "Your usage of dmriprep is being recorded using popylar (https://popylar.github.io/). ",  # noqa
            "For details, see https://nipreps.github.io/dmriprep/usage.html. ",
            "To opt out, call dmriprep with a `--notrack` flag",
        )
        popylar.track_event(__ga_id__, "run", "cli_run")

    # CRITICAL Save the config to a file. This is necessary because the execution graph
    # is built as a separate process to keep the memory footprint low. The most
    # straightforward way to communicate with the child process is via the filesystem.
    config_file = config.execution.work_dir / ".dmriprep.toml"
    config.to_filename(config_file)

    # CRITICAL Call build_workflow(config_file, retval) in a subprocess.
    # Because Python on Linux does not ever free virtual memory (VM), running the
    # workflow construction jailed within a process preempts excessive VM buildup.
    with Manager() as mgr:
        from .workflow import build_workflow

        retval = mgr.dict()
        p = Process(target=build_workflow, args=(str(config_file), retval))
        p.start()
        p.join()

        retcode = p.exitcode or retval.get("return_code", 0)
        dmriprep_wf = retval.get("workflow", None)

    # CRITICAL Load the config from the file. This is necessary because the ``build_workflow``
    # function executed constrained in a process may change the config (and thus the global
    # state of dMRIPrep).
    config.load(config_file)

    if config.execution.reports_only:
        sys.exit(int(retcode > 0))

    if dmriprep_wf and config.execution.write_graph:
        dmriprep_wf.write_graph(graph2use="colored", format="svg", simple_form=True)

    retcode = retcode or (dmriprep_wf is None) * os.EX_SOFTWARE
    if retcode != 0:
        sys.exit(retcode)

    # Generate boilerplate
    with Manager() as mgr:
        from .workflow import build_boilerplate

        p = Process(target=build_boilerplate, args=(str(config_file), dmriprep_wf))
        p.start()
        p.join()

    if config.execution.boilerplate_only:
        sys.exit(int(retcode > 0))

    # Clean up master process before running workflow, which may create forks
    gc.collect()

    if popylar is not None:
        popylar.track_event(__ga_id__, "run", "started")

    config.loggers.workflow.log(
        15,
        "\n".join(
            ["dMRIPrep config:"] + ["\t\t%s" % s for s in config.dumps().splitlines()]
        ),
    )
    config.loggers.workflow.log(25, "dMRIPrep started!")
    errno = 1  # Default is error exit unless otherwise set
    try:
        dmriprep_wf.run(**config.nipype.get_plugin())
    except Exception as e:
        if not config.execution.notrack:
            popylar.track_event(__ga_id__, "run", "error")
        config.loggers.workflow.critical("dMRIPrep failed: %s", e)
        raise
    else:
        config.loggers.workflow.log(25, "dMRIPrep finished successfully!")

        # Bother users with the boilerplate only iff the workflow went okay.
        if (config.execution.output_dir / "dmriprep" / "logs" / "CITATION.md").exists():
            config.loggers.workflow.log(
                25,
                "Works derived from this dMRIPrep execution should "
                "include the following boilerplate: "
                f"{config.execution.output_dir / 'dmriprep' / 'logs' / 'CITATION.md'}."
            )

        if config.workflow.run_reconall:
            from templateflow import api
            from niworkflows.utils.misc import _copy_any

            dseg_tsv = str(api.get("fsaverage", suffix="dseg", extension=[".tsv"]))
            _copy_any(
                dseg_tsv,
                str(config.execution.output_dir / "dmriprep" / "desc-aseg_dseg.tsv"),
            )
            _copy_any(
                dseg_tsv,
                str(
                    config.execution.output_dir / "dmriprep" / "desc-aparcaseg_dseg.tsv"
                ),
            )
        errno = 0
    finally:
        from niworkflows.reports import generate_reports
        from pkg_resources import resource_filename as pkgrf

        # Generate reports phase
        failed_reports = generate_reports(
            config.execution.participant_label,
            config.execution.output_dir,
            config.execution.run_uuid,
            config=pkgrf("dmriprep", "config/reports-spec.yml"),
            packagename="dmriprep",
        )
        write_derivative_description(
            config.execution.bids_dir, config.execution.output_dir / "dmriprep"
        )

        if failed_reports and not config.execution.notrack:
            popylar.track_event(__ga_id__, "run", "reporting_error")
        sys.exit(int((errno + failed_reports) > 0))


if __name__ == "__main__":
    raise RuntimeError(
        "dmriprep/cli/run.py should not be run directly;\n"
        "Please `pip install` dmriprep and use the `dmriprep` command"
    )
