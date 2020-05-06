# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parser."""
import os
import sys
from .. import config


def _build_parser():
    """Build parser object."""
    from functools import partial
    from pathlib import Path
    from argparse import (
        ArgumentParser,
        ArgumentDefaultsHelpFormatter,
    )
    from packaging.version import Version
    from .version import check_latest, is_flagged
    from niworkflows.utils.spaces import Reference, OutputReferencesAction

    def _path_exists(path, parser):
        """Ensure a given path exists."""
        if path is None or not Path(path).exists():
            raise parser.error(f"Path does not exist: <{path}>.")
        return Path(path).absolute()

    def _min_one(value, parser):
        """Ensure an argument is not lower than 1."""
        value = int(value)
        if value < 1:
            raise parser.error("Argument can't be less than one.")
        return value

    def _to_gb(value):
        scale = {"G": 1, "T": 10 ** 3, "M": 1e-3, "K": 1e-6, "B": 1e-9}
        digits = "".join([c for c in value if c.isdigit()])
        units = value[len(digits):] or "M"
        return int(digits) * scale[units[0]]

    def _drop_sub(value):
        value = str(value)
        return value.lstrip("sub-")

    def _bids_filter(value):
        from json import loads

        if value and Path(value).exists():
            return loads(Path(value).read_text())

    verstr = f"dMRIPrep v{config.environment.version}"
    currentv = Version(config.environment.version)
    is_release = not any(
        (currentv.is_devrelease, currentv.is_prerelease, currentv.is_postrelease)
    )

    parser = ArgumentParser(
        description="dMRIPrep: dMRI PREProcessing workflows v{}".format(
            config.environment.version
        ),
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    PathExists = partial(_path_exists, parser=parser)
    PositiveInt = partial(_min_one, parser=parser)

    # Arguments as specified by BIDS-Apps
    # required, positional arguments
    # IMPORTANT: they must go directly with the parser object
    parser.add_argument(
        "bids_dir",
        action="store",
        type=PathExists,
        help="the root folder of a BIDS valid dataset (sub-XXXXX folders should "
        "be found at the top level in this folder).",
    )
    parser.add_argument(
        "output_dir",
        action="store",
        type=Path,
        help="the output path for the outcomes of preprocessing and visual " "reports",
    )
    parser.add_argument(
        "analysis_level",
        choices=["participant"],
        help='processing stage to be run, only "participant" in the case of '
        "dMRIPrep (see BIDS-Apps specification).",
    )

    # optional arguments
    parser.add_argument("--version", action="version", version=verstr)

    g_bids = parser.add_argument_group("Options for filtering BIDS queries")
    g_bids.add_argument(
        "--skip-bids-validation",
        action="store_true",
        default=False,
        help="assume the input dataset is BIDS compliant and skip the validation",
    )
    g_bids.add_argument(
        "--participant-label",
        "--participant_label",
        action="store",
        nargs="+",
        type=_drop_sub,
        help="a space delimited list of participant identifiers or a single "
        "identifier (the sub- prefix can be removed)",
    )
    g_bids.add_argument(
        "--bids-filter-file",
        dest="bids_filters",
        action="store",
        type=_bids_filter,
        metavar="PATH",
        help="a JSON file describing custom BIDS input filter using pybids "
        "{<suffix>:{<entity>:<filter>,...},...} "
        "(https://github.com/bids-standard/pybids/blob/master/bids/layout/config/bids.json)",
    )
    g_bids.add_argument(
        "--anat-derivatives", action='store', metavar="PATH", type=PathExists,
        help="Reuse the anatomical derivatives from another fMRIPrep run or calculated "
             "with an alternative processing tool (NOT RECOMMENDED)."
    )

    g_perfm = parser.add_argument_group("Options to handle performance")
    g_perfm.add_argument(
        "--nprocs",
        "--nthreads",
        "--n_cpus",
        "-n-cpus",
        action="store",
        type=PositiveInt,
        help="maximum number of threads across all processes",
    )
    g_perfm.add_argument(
        "--omp-nthreads",
        action="store",
        type=PositiveInt,
        help="maximum number of threads per-process",
    )
    g_perfm.add_argument(
        "--mem",
        "--mem_mb",
        "--mem-mb",
        dest="memory_gb",
        action="store",
        type=_to_gb,
        help="upper bound memory limit for dMRIPrep processes",
    )
    g_perfm.add_argument(
        "--low-mem",
        action="store_true",
        help="attempt to reduce memory usage (will increase disk usage "
        "in working directory)",
    )
    g_perfm.add_argument(
        "--use-plugin",
        action="store",
        default=None,
        help="nipype plugin configuration file",
    )
    g_perfm.add_argument(
        "--anat-only", action="store_true", help="run anatomical workflows only"
    )
    g_perfm.add_argument(
        "--boilerplate_only",
        action="store_true",
        default=False,
        help="generate boilerplate only",
    )
    g_perfm.add_argument(
        "--md-only-boilerplate",
        action="store_true",
        default=False,
        help="skip generation of HTML and LaTeX formatted citation with pandoc",
    )
    g_perfm.add_argument(
        "-v",
        "--verbose",
        dest="verbose_count",
        action="count",
        default=0,
        help="increases log verbosity for each occurrence, debug level is -vvv",
    )

    g_conf = parser.add_argument_group("Workflow configuration")
    g_conf.add_argument(
        "--ignore",
        required=False,
        action="store",
        nargs="+",
        default=[],
        choices=["fieldmaps", "slicetiming", "sbref"],
        help="ignore selected aspects of the input dataset to disable corresponding "
        "parts of the workflow (a space delimited list)",
    )
    g_conf.add_argument(
        "--longitudinal",
        action="store_true",
        help="treat dataset as longitudinal - may increase runtime",
    )
    g_conf.add_argument(
        "--output-spaces",
        nargs="*",
        action=OutputReferencesAction,
        help="""\
Standard and non-standard spaces to resample anatomical and functional images to. \
Standard spaces may be specified by the form \
``<SPACE>[:cohort-<label>][:res-<resolution>][...]``, where ``<SPACE>`` is \
a keyword designating a spatial reference, and may be followed by optional, \
colon-separated parameters. \
Non-standard spaces imply specific orientations and sampling grids. \
The default value of this flag (meaning, if the argument is not include in the command line) \
is ``--output-spaces run`` - the original space and sampling grid of the original DWI run. \
Important to note, the ``res-*`` modifier does not define the resolution used for \
the spatial normalization. To generate no DWI outputs (if that is intended for some reason), \
use this option without specifying any spatial references. For further details, please check out \
https://www.nipreps.org/dmriprep/en/%s/spaces.html"""
        % (currentv.base_version if is_release else "latest"),
    )

    #  ANTs options
    g_ants = parser.add_argument_group("Specific options for ANTs registrations")
    g_ants.add_argument(
        "--skull-strip-template",
        default="OASIS30ANTs",
        type=Reference.from_string,
        help="select a template for skull-stripping with antsBrainExtraction",
    )
    g_ants.add_argument(
        "--skull-strip-fixed-seed",
        action="store_true",
        help="do not use a random seed for skull-stripping - will ensure "
        "run-to-run replicability when used with --omp-nthreads 1",
    )

    # Fieldmap options
    g_fmap = parser.add_argument_group("Specific options for handling fieldmaps")
    g_fmap.add_argument(
        "--fmap-bspline",
        action="store_true",
        default=False,
        help="fit a B-Spline field using least-squares (experimental)",
    )
    g_fmap.add_argument(
        "--fmap-no-demean",
        action="store_false",
        default=True,
        help="do not remove median (within mask) from fieldmap",
    )

    # SyN-unwarp options
    g_syn = parser.add_argument_group("Specific options for SyN distortion correction")
    g_syn.add_argument(
        "--use-syn-sdc",
        action="store_true",
        default=False,
        help="EXPERIMENTAL: Use fieldmap-free distortion correction",
    )
    g_syn.add_argument(
        "--force-syn",
        action="store_true",
        default=False,
        help="EXPERIMENTAL/TEMPORARY: Use SyN correction in addition to "
        "fieldmap correction, if available",
    )

    # FreeSurfer options
    g_fs = parser.add_argument_group("Specific options for FreeSurfer preprocessing")
    g_fs.add_argument(
        "--fs-license-file",
        metavar="PATH",
        type=PathExists,
        help="Path to FreeSurfer license key file. Get it (for free) by registering"
        " at https://surfer.nmr.mgh.harvard.edu/registration.html",
    )
    g_fs.add_argument(
        "--fs-subjects-dir",
        metavar="PATH",
        type=Path,
        help="Path to existing FreeSurfer subjects directory to reuse. "
        "(default: OUTPUT_DIR/freesurfer)",
    )

    # Surface generation xor
    g_surfs = parser.add_argument_group("Surface preprocessing options")
    g_surfs_xor = g_surfs.add_mutually_exclusive_group()
    g_surfs_xor.add_argument(
        "--no-submm-recon",
        action="store_false",
        dest="hires",
        help="disable sub-millimeter (hires) reconstruction",
    )
    g_surfs_xor.add_argument(
        "--fs-no-reconall",
        action="store_false",
        dest="run_reconall",
        help="disable FreeSurfer surface preprocessing.",
    )

    g_other = parser.add_argument_group("Other options")
    g_other.add_argument(
        "-w",
        "--work-dir",
        action="store",
        type=Path,
        default=Path("work").absolute(),
        help="path where intermediate results should be stored",
    )
    g_other.add_argument(
        "--clean-workdir",
        action="store_true",
        default=False,
        help="Clears working directory of contents. Use of this flag is not"
        "recommended when running concurrent processes of dMRIPrep.",
    )
    g_other.add_argument(
        "--resource-monitor",
        action="store_true",
        default=False,
        help="enable Nipype's resource monitoring to keep track of memory and CPU usage",
    )
    g_other.add_argument(
        "--reports-only",
        action="store_true",
        default=False,
        help="only generate reports, don't run workflows. This will only rerun report "
        "aggregation, not reportlet generation for specific nodes.",
    )
    g_other.add_argument(
        "--run-uuid",
        action="store",
        default=None,
        help="Specify UUID of previous run, to include error logs in report. "
        "No effect without --reports-only.",
    )
    g_other.add_argument(
        "--write-graph",
        action="store_true",
        default=False,
        help="Write workflow graph.",
    )
    g_other.add_argument(
        "--stop-on-first-crash",
        action="store_true",
        default=False,
        help="Force stopping on first crash, even if a work directory"
        " was specified.",
    )
    g_other.add_argument(
        "--notrack",
        action="store_true",
        default=False,
        help="Opt-out of sending tracking information of this run to "
        "the dMRIPREP developers. This information helps to "
        "improve dMRIPREP and provides an indicator of real "
        "world usage crucial for obtaining funding.",
    )
    g_other.add_argument(
        "--sloppy",
        dest="debug",
        action="store_true",
        default=False,
        help="Use low-quality tools for speed - TESTING ONLY",
    )

    latest = check_latest()
    if latest is not None and currentv < latest:
        print(
            """\
You are using dMRIPrep-%s, and a newer version of dMRIPrep is available: %s.
Please check out our documentation about how and when to upgrade:
https://dmriprep.readthedocs.io/en/latest/faq.html#upgrading"""
            % (currentv, latest),
            file=sys.stderr,
        )

    _blist = is_flagged()
    if _blist[0]:
        _reason = _blist[1] or "unknown"
        print(
            """\
WARNING: Version %s of dMRIPrep (current) has been FLAGGED
(reason: %s).
That means some severe flaw was found in it and we strongly
discourage its usage."""
            % (config.environment.version, _reason),
            file=sys.stderr,
        )

    return parser


def parse_args(args=None, namespace=None):
    """Parse args and run further checks on the command line."""
    import logging
    from niworkflows.utils.spaces import Reference, SpatialReferences

    parser = _build_parser()
    opts = parser.parse_args(args, namespace)
    config.execution.log_level = int(max(25 - 5 * opts.verbose_count, logging.DEBUG))
    config.from_dict(vars(opts))
    config.loggers.init()

    # Initialize --output-spaces if not defined
    if config.execution.output_spaces is None:
        config.execution.output_spaces = SpatialReferences([Reference("run")])

    # Retrieve logging level
    build_log = config.loggers.cli

    if config.execution.fs_license_file is None:
        raise RuntimeError(
            """\
ERROR: a valid license file is required for FreeSurfer to run. dMRIPrep looked for an existing \
license file at several paths, in this order: 1) command line argument ``--fs-license-file``; \
2) ``$FS_LICENSE`` environment variable; and 3) the ``$FREESURFER_HOME/license.txt`` path. Get it \
(for free) by registering at https://surfer.nmr.mgh.harvard.edu/registration.html"""
        )
    os.environ["FS_LICENSE"] = str(config.execution.fs_license_file)

    # Load base plugin_settings from file if --use-plugin
    if opts.use_plugin is not None:
        from yaml import load as loadyml

        with open(opts.use_plugin) as f:
            plugin_settings = loadyml(f)
        _plugin = plugin_settings.get("plugin")
        if _plugin:
            config.nipype.plugin = _plugin
            config.nipype.plugin_args = plugin_settings.get("plugin_args", {})
            config.nipype.nprocs = config.nipype.plugin_args.get(
                "nprocs", config.nipype.nprocs
            )

    # Resource management options
    # Note that we're making strong assumptions about valid plugin args
    # This may need to be revisited if people try to use batch plugins
    if 1 < config.nipype.nprocs < config.nipype.omp_nthreads:
        build_log.warning(
            "Per-process threads (--omp-nthreads=%d) exceed total "
            "threads (--nthreads/--n_cpus=%d)",
            config.nipype.omp_nthread,
            config.nipype.nprocs,
        )

    bids_dir = config.execution.bids_dir
    output_dir = config.execution.output_dir
    work_dir = config.execution.work_dir
    version = config.environment.version

    if config.execution.fs_subjects_dir is None:
        config.execution.fs_subjects_dir = output_dir / "freesurfer"

    # Wipe out existing work_dir
    if opts.clean_workdir and work_dir.exists():
        from niworkflows.utils.misc import clean_directory

        build_log.log("Clearing previous dMRIPrep working directory: %s", work_dir)
        if not clean_directory(work_dir):
            build_log.warning(
                "Could not clear all contents of working directory: %s", work_dir
            )

    # Ensure input and output folders are not the same
    if output_dir == bids_dir:
        parser.error(
            "The selected output folder is the same as the input BIDS folder. "
            "Please modify the output path (suggestion: %s)."
            % bids_dir
            / "derivatives"
            / ("dmriprep-%s" % version.split("+")[0])
        )

    if bids_dir in work_dir.parents:
        parser.error(
            "The selected working directory is a subdirectory of the input BIDS folder. "
            "Please modify the output path."
        )

    # Validate inputs
    if not opts.skip_bids_validation:
        from ..utils.bids import validate_input_dir

        build_log.info(
            "Making sure the input data is BIDS compliant (warnings can be ignored in most "
            "cases)."
        )
        validate_input_dir(
            config.environment.exec_env, opts.bids_dir, opts.participant_label
        )

    # Setup directories
    config.execution.log_dir = output_dir / "dmriprep" / "logs"
    # Check and create output and working directories
    config.execution.log_dir.mkdir(exist_ok=True, parents=True)
    output_dir.mkdir(exist_ok=True, parents=True)
    work_dir.mkdir(exist_ok=True, parents=True)

    # Force initialization of the BIDSLayout
    config.execution.init()
    all_subjects = config.execution.layout.get_subjects()
    if config.execution.participant_label is None:
        config.execution.participant_label = all_subjects

    participant_label = set(config.execution.participant_label)
    missing_subjects = participant_label - set(all_subjects)
    if missing_subjects:
        parser.error(
            "One or more participant labels were not found in the BIDS directory: "
            "%s." % ", ".join(missing_subjects)
        )

    config.execution.participant_label = sorted(participant_label)
    config.workflow.skull_strip_template = config.workflow.skull_strip_template[0]
