#!/usr/bin/env python
"""dMRI preprocessing workflow."""

from pathlib import Path
import sys
import uuid
import warnings
warnings.filterwarnings("ignore")
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
from multiprocessing import cpu_count
from time import strftime


def get_parser():
    """Build parser object"""
    from packaging.version import Version
    from dmriprep.__about__ import __version__
    from dmriprep.cli.version import check_latest, is_flagged

    verstr = 'dmriprep v{}'.format(__version__)
    currentv = Version(__version__)
    is_release = not any((currentv.is_devrelease, currentv.is_prerelease, currentv.is_postrelease))

    parser = ArgumentParser(description='dMRIPrep: dMRI PREProcessing workflows',
                            formatter_class=ArgumentDefaultsHelpFormatter)

    # Arguments as specified by BIDS-Apps
    # required, positional arguments
    # IMPORTANT: they must go directly with the parser object
    parser.add_argument('bids_dir', action='store', type=Path,
                        help='The root folder of a BIDS valid dataset (sub-XXXXX folders should '
                             'be found at the top level in this folder).')
    parser.add_argument('output_dir', action='store', type=Path,
                        help='The output path for the outcomes of preprocessing and visual '
                             'reports')
    parser.add_argument('analysis_level', choices=['participant'],
                        help='Processing stage to be run, only "participant" in the case of '
                             'dMRIPrep (see BIDS-Apps specification).')

    # optional arguments
    parser.add_argument('--version', action='version', version=verstr)

    g_bids = parser.add_argument_group('Options for filtering BIDS queries')
    g_bids.add_argument('--skip_bids_validation', action='store_true', default=False,
                        help='Assume the input dataset is BIDS compliant and skip the validation')
    g_bids.add_argument('--participant_label', action='store', nargs='+',
                        help='A space delimited list of participant identifiers or a single '
                             'identifier (the sub- prefix can be removed)')
    g_bids.add_argument('-s', '--session_id', action='store', nargs='+',
                        help='A space delimited list of session identifiers or a single '
                             'identifier (the ses- prefix can be removed)')
    g_perfm = parser.add_argument_group('Options to handle performance')
    g_perfm.add_argument('--plugin', action='store', type=str, default='MultiProc',
                         help='Plugin type. Options include MultiProc or Linear')
    g_perfm.add_argument('--nprocs', '--n_cpus', action='store', type=int, default=8,
                         help='Maximum number of threads across all processes. Minimum required is 8.')
    g_perfm.add_argument('--omp_nthreads', action='store', type=int, default=2,
                         help='Maximum number of threads per-process')
    g_perfm.add_argument('--mem_gb', action='store', default=16, type=int,
                         help='Upper bound memory limit for dMRIPrep processes. Minimum required is 16 GB.')
    g_perfm.add_argument("-v", "--verbose", action="store_true", default=False,
                         help="Perform debug and logging.")

    g_conf = parser.add_argument_group('Workflow configuration')
    g_conf.add_argument('--sdc_method', action='store', default='topup',
                        help='Susceptibility distortion correction type')
    g_conf.add_argument('--denoise_strategy', action='store', default='mppca',
                        help='Denoising strategy. Choices include: mppca, nlmeans, localpca, and nlsam')
    g_conf.add_argument('--outlier_threshold', action='store', default=0.02,
                        help='Percent of bad slices required to reject volume.')
    g_conf.add_argument('--vox_size', action='store', default='1mm',
                        help='Voxel resolution in mm.')

    g_other = parser.add_argument_group('Other options')
    g_other.add_argument('-w', '--work_dir', action='store', type=Path, default=Path('/tmp/work'),
                         help='Path where intermediate results should be stored. Default is /tmp/work')
    g_other.add_argument('--write_graph', action='store_true', default=False,
                         help='Write workflow graph.')

    latest = check_latest()
    if latest is not None and currentv < latest:
        print("""You are using dMRIPrep-%s, and a newer version of dMRIPrep is available: %s. 
        Please check out our documentation about how and when to upgrade: 
        https://dmriprep.readthedocs.io/en/latest/faq.html#upgrading""" % (
            __version__, latest), file=sys.stderr)

    _blist = is_flagged()
    if _blist[0]:
        _reason = _blist[1] or 'unknown'
        print("""WARNING: Version %s of dMRIPrep (current) has been FLAGGED (reason: %s). 
        That means some severe flaw was found in it and we strongly 
        discourage its usage.""" % (__version__, _reason), file=sys.stderr)

    return parser


def build_workflow(opts, retval):
    import numpy as np
    import shutil
    import os
    from bids import BIDSLayout
    from dmriprep.__about__ import __version__
    from dmriprep.workflows.dwi.base import init_base_wf
    from dmriprep.utils.bids import collect_sessions, get_bids_dict

    INIT_MSG = """
    Running dMRIPrep version {version}:
      * BIDS dataset path: {bids_dir}.
      * Participant list: {subject}.
      * Session list: {session}.
      * Run identifier: {uuid}.
    """.format

    bids_dir = opts.bids_dir.resolve()
    output_dir = opts.output_dir.resolve()
    work_dir = opts.work_dir.resolve()

    retval['return_code'] = 1
    retval['workflow'] = None
    retval['bids_dir'] = str(bids_dir)
    retval['output_dir'] = str(output_dir)
    retval['work_dir'] = str(work_dir)

    if output_dir == bids_dir:
        ValueError(
            'The selected output folder is the same as the input BIDS folder. '
            'Please modify the output path (suggestion: %s).',
            bids_dir / 'derivatives' / ('dmriprep-%s' % __version__.split('+')[0]))
        retval['return_code'] = 1
        return retval

    # Set up some instrumental utilities
    run_uuid = '%s_%s' % (strftime('%Y%m%d-%H%M%S'), uuid.uuid4())
    retval['run_uuid'] = run_uuid

    # First check that bids_dir looks like a BIDS folder
    if opts.skip_bids_validation is True:
        validate = False
    else:
        validate = True
    layout = BIDSLayout(str(bids_dir), validate=validate)
    bids_dict = get_bids_dict(layout, opts.participant_label, opts.session_id)
    subjects_list = list(list(bids_dict.keys())[0])
    session_list = list(list(bids_dict.values())[0].keys())
    retval['subject_list'] = subjects_list
    retval['session_list'] = session_list

    # Resource management options
    omp_nthreads = opts.omp_nthreads
    mem_gb = opts.mem_gb
    nprocs = opts.nprocs
    if nprocs is None:
        nprocs = cpu_count()

    if omp_nthreads == 0:
        omp_nthreads = int(np.round(min(float(nprocs) - 1 if float(nprocs) > 1 else cpu_count(), 8)), 0)

    if 1 < float(nprocs) < float(omp_nthreads):
        raise RuntimeWarning('Per-process threads (--omp_nthreads=%d) exceed total threads (--nprocs/--n_cpus=%d)',
                             omp_nthreads, nprocs)

    # Set up directories
    log_dir = output_dir / 'dmriprep' / 'logs'

    # Check and create output and working directories
    output_dir.mkdir(exist_ok=True, parents=True)
    log_dir.mkdir(exist_ok=True, parents=True)
    work_dir.mkdir(exist_ok=True, parents=True)

    uuid_dir = str(work_dir) + '/' + str(run_uuid)
    if os.path.exists(uuid_dir):
        shutil.rmtree(uuid_dir)
    os.mkdir(uuid_dir)

    # Single-subject pipeline
    wf = init_base_wf(
            bids_dict=bids_dict,
            output_dir=str(output_dir),
            sdc_method=opts.sdc_method,
            denoise_strategy=opts.denoise_strategy,
            vox_size=opts.vox_size,
            outlier_thresh=opts.outlier_threshold,
            omp_nthreads=omp_nthreads,
            work_dir=uuid_dir
        )

    wf.base_dir = uuid_dir

    if opts.verbose is True:
        from nipype import config, logging
        cfg_v = dict(logging={'workflow_level': 'DEBUG', 'utils_level': 'DEBUG', 'interface_level': 'DEBUG',
                              'log_directory': str(log_dir), 'log_to_file': True},
                     monitoring={'enabled': True, 'sample_frequency': '0.1', 'summary_append': True,
                                 'summary_file': str(wf.base_dir)})
        logging.update_logging(config)
        config.update_config(cfg_v)
        config.enable_debug_mode()
        config.enable_resource_monitor()

        import logging
        callback_log_path = "%s%s" % (wf.base_dir, '/run_stats.log')
        logger = logging.getLogger('callback')
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(callback_log_path)
        logger.addHandler(handler)

    # Set runtime/logging configurations
    plugin_type = opts.plugin
    cfg = dict(
        execution={
            "stop_on_first_crash": False,
            "hash_method": "content",
            "crashfile_format": "txt",
            "display_variable": ":0",
            "job_finished_timeout": 65,
            "matplotlib_backend": "Agg",
            "plugin": plugin_type,
            "use_relative_paths": True,
            "parameterize_dirs": True,
            "remove_unnecessary_outputs": False,
            "remove_node_directories": False,
            "poll_sleep_duration": 0.1,
        }
    )
    for key in cfg.keys():
        for setting, value in cfg[key].items():
            wf.config[key][setting] = value
    try:
        wf.write_graph(graph2use="colored", format='png')
    except:
        pass

    if opts.verbose is True:
        from nipype.utils.profiler import log_nodes_cb
        plugin_args = {'n_procs': int(nprocs),
                       'memory_gb': int(mem_gb),
                       'status_callback': log_nodes_cb}
    else:
        plugin_args = {'n_procs': int(nprocs),
                       'memory_gb': int(mem_gb)}
    print("%s%s%s" % ('\nRunning with ', str(plugin_args), '\n'))
    wf.run(plugin=str(plugin_type), plugin_args=plugin_args)
    retval['return_code'] = 0

    if opts.verbose is True:
        from nipype.utils.draw_gantt_chart import generate_gantt_chart
        print('Plotting resource profile from run...')
        generate_gantt_chart("%s%s" % (wf.base_dir, '/run_stats.log'),
                             cores=int(nprocs))
        handler.close()
        logger.removeHandler(handler)

    return


def main():
    """Initializes main script from command-line call to generate single-subject or multi-subject workflow(s)"""
    import sys
    try:
        import dmriprep
    except ImportError:
        print('dmriprep not installed! Ensure that you are referencing the correct site-packages and using Python3.5+')

    if len(sys.argv) < 1:
        print("\nMissing command-line inputs! See help options with the -h flag.\n")
        sys.exit()

    opts = get_parser().parse_args()

    try:
        from multiprocessing import set_start_method, Process, Manager
        set_start_method('forkserver')
        with Manager() as mgr:
            retval = mgr.dict()
            p = Process(target=build_workflow, args=(opts, retval))
            p.start()
            p.join()

            if p.exitcode != 0:
                sys.exit(p.exitcode)
    except:
        print('\nWARNING: Forkserver failed to initialize. Are you using Python3 ?')
        retval = dict()
        build_workflow(opts, retval)


if __name__ == '__main__':
    __spec__ = "ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>)"
    main()
