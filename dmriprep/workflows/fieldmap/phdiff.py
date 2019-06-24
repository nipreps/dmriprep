#!/usr/bin/env python

"""
.. _sdc_phasediff :
Phase-difference B0 estimation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The field inhomogeneity inside the scanner (fieldmap) is proportional to the
phase drift between two subsequent :abbr:`GRE (gradient recall echo)`
sequence.
Fieldmap preprocessing workflow for fieldmap data structure
8.9.1 in BIDS 1.0.0: one phase diff and at least one magnitude image
8.9.2 in BIDS 1.0.0: two phases and at least one magnitude image
"""

from nipype.interfaces import ants, fsl, utility as niu
from nipype.pipeline import engine as pe
from nipype.workflows.dmri.fsl.utils import siemens2rads, demean_image, \
    cleanup_edge_pipeline
#from niworkflows.engine.workflows import LiterateWorkflow as Workflow
#from niworkflows.interfaces.bids import ReadSidecarJSON
#from niworkflows.interfaces.images import IntraModalMerge
#from niworkflows.interfaces.masks import BETRPT

from ...interfaces import Phasediff2Fieldmap, Phases2Fieldmap

def init_phdiff_wf(omp_nthreads, layout, phasetype='phasediff', name='phdiff_wf'):
    """
    Estimates the fieldmap using a phase-difference image and one or more
    magnitude images corresponding to two or more :abbr:`GRE (Gradient Echo sequence)`
    acquisitions. The `original code was taken from nipype
    <https://github.com/nipy/nipype/blob/master/nipype/workflows/dmri/fsl/artifacts.py#L514>`_.
    .. workflow ::
        :graph2use: orig
        :simple_form: yes
        from fmriprep.workflows.fieldmap.phdiff import init_phdiff_wf
        wf = init_phdiff_wf(omp_nthreads=1)
    Outputs::
      outputnode.fmap_ref - The average magnitude image, skull-stripped
      outputnode.fmap_mask - The brain mask applied to the fieldmap
      outputnode.fmap - The estimated fieldmap in Hz
    """

    workflow = pe.Workflow(name=name)
    '''
    workflow.__desc__ = """\
A deformation field to correct for susceptibility distortions was estimated
based on a field map that was co-registered to the BOLD reference,
using a custom workflow of *fMRIPrep* derived from D. Greve's `epidewarp.fsl`
[script](http://www.nmr.mgh.harvard.edu/~greve/fbirn/b0/epidewarp.fsl) and
further improvements of HCP Pipelines [@hcppipelines].
"""
    '''
    inputnode = pe.Node(niu.IdentityInterface(fields=['magnitude', 'phasediff']),
                        name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['fmap', 'fmap_ref', 'fmap_mask']), name='outputnode')

    # Merge input magnitude images
    magmrg = pe.Node(IntraModalMerge(), name='magmrg')

    # de-gradient the fields ("bias/illumination artifact")
    n4 = pe.Node(ants.N4BiasFieldCorrection(dimension=3, copy_header=True),
                 name='n4', n_procs=omp_nthreads)
    #bet = pe.Node(BETRPT(generate_report=True, frac=0.6, mask=True),
    #              name='bet')
    bet = pe.Node(fsl.BET(frac=0.6, mask=True),
                  name='bet')
    ds_report_fmap_mask = pe.Node(DerivativesDataSink(
        desc='brain', suffix='mask'), name='ds_report_fmap_mask',
        mem_gb=0.01, run_without_submitting=True)
    # uses mask from bet; outputs a mask
    # dilate = pe.Node(fsl.maths.MathsCommand(
    #     nan2zeros=True, args='-kernel sphere 5 -dilM'), name='MskDilate')

    # FSL PRELUDE will perform phase-unwrapping
    prelude = pe.Node(fsl.PRELUDE(), name='prelude')

    denoise = pe.Node(fsl.SpatialFilter(operation='median', kernel_shape='sphere',
                                        kernel_size=3), name='denoise')

    demean = pe.Node(niu.Function(function=demean_image), name='demean')

    cleanup_wf = cleanup_edge_pipeline(name="cleanup_wf")

    compfmap = pe.Node(Phasediff2Fieldmap(), name='compfmap')
    compfmap.inputs.metadata = metadata

    # The phdiff2fmap interface is equivalent to:
    # rad2rsec (using rads2radsec from nipype.workflows.dmri.fsl.utils)
    # pre_fugue = pe.Node(fsl.FUGUE(save_fmap=True), name='ComputeFieldmapFUGUE')
    # rsec2hz (divide by 2pi)

    if phasetype == "phasediff":
        # Read phasediff echo times
        meta = pe.Node(ReadSidecarJSON(bids_validate=False), name='meta', mem_gb=0.01)

        # phase diff -> radians
        pha2rads = pe.Node(niu.Function(function=siemens2rads),
                           name='pha2rads')
        # Read phasediff echo times
        meta = pe.Node(ReadSidecarJSON(), name='meta', mem_gb=0.01,
                       run_without_submitting=True)
        workflow.connect([
            #(meta, compfmap, [('out_dict', 'metadata')]),
            (inputnode, pha2rads, [('phasediff', 'in_file')]),
            (pha2rads, prelude, [('out', 'phase_file')]),
            (inputnode, ds_report_fmap_mask, [('phasediff', 'source_file')]),
        ])

    elif phasetype == "phase":
        workflow.__desc__ += """\
The phase difference used for unwarping was calculated using two separate phase measurements
 [@pncprocessing].
    """
        # Special case for phase1, phase2 images
        meta = pe.MapNode(ReadSidecarJSON(), name='meta', mem_gb=0.01,
                          run_without_submitting=True, iterfield=['in_file'])
        phases2fmap = pe.Node(Phases2Fieldmap(), name='phases2fmap')
        workflow.connect([
            (meta, phases2fmap, [('out_dict', 'metadatas')]),
            (inputnode, phases2fmap, [('phasediff', 'phase_files')]),
            (phases2fmap, prelude, [('out_file', 'phase_file')]),
            (phases2fmap, compfmap, [('phasediff_metadata', 'metadata')]),
            (phases2fmap, ds_report_fmap_mask, [('out_file', 'source_file')])
        ])

    workflow.connect([
        (inputnode, meta, [('phasediff', 'in_file')]),
        (inputnode, magmrg, [('magnitude', 'in_files')]),
        (magmrg, n4, [('out_avg', 'input_image')]),
        (n4, prelude, [('output_image', 'magnitude_file')]),
        (n4, bet, [('output_image', 'in_file')]),
        (bet, prelude, [('mask_file', 'mask_file')]),
        (prelude, denoise, [('unwrapped_phase_file', 'in_file')]),
        (denoise, demean, [('out_file', 'in_file')]),
        (demean, cleanup_wf, [('out', 'inputnode.in_file')]),
        (bet, cleanup_wf, [('mask_file', 'inputnode.in_mask')]),
        (cleanup_wf, compfmap, [('outputnode.out_file', 'in_file')]),
        (compfmap, outputnode, [('out_file', 'fmap')]),
        (bet, outputnode, [('mask_file', 'fmap_mask'),
                           ('out_file', 'fmap_ref')]),
        (bet, ds_report_fmap_mask, [('out_report', 'in_file')]),
    ])

    return workflow

class ReadSidecarJSONInputSpec(BIDSBaseInputSpec):
    in_file = File(exists=True, mandatory=True, desc='the input nifti file')


class ReadSidecarJSONOutputSpec(BIDSInfoOutputSpec):
    out_dict = traits.Dict()


class ReadSidecarJSON(SimpleInterface):
    input_spec = ReadSidecarJSONInputSpec
    output_spec = ReadSidecarJSONOutputSpec
    layout = None
    _always_run = True

    def __init__(self, fields=None, undef_fields=False, **inputs):
        super(ReadSidecarJSON, self).__init__(**inputs)
        self._fields = fields or []
        if isinstance(self._fields, str):
            self._fields = [self._fields]

        self._undef_fields = undef_fields

    def _outputs(self):
        base = super(ReadSidecarJSON, self)._outputs()
        if self._fields:
            base = add_traits(base, self._fields)
        return base

    def _run_interface(self, runtime):
        self.layout = self.inputs.bids_dir or self.layout
        self.layout = _init_layout(self.inputs.in_file,
                                   self.layout,
                                   self.inputs.bids_validate)

        # Fill in BIDS entities of the output ("*_id")
        output_keys = list(BIDSInfoOutputSpec().get().keys())
        params = self.layout.parse_file_entities(self.inputs.in_file)
        self._results = {key: params.get(key.split('_')[0], Undefined)
                         for key in output_keys}

        # Fill in metadata
        metadata = self.layout.get_metadata(self.inputs.in_file)
        self._results['out_dict'] = metadata

        # Set dynamic outputs if fields input is present
        for fname in self._fields:
            if not self._undef_fields and fname not in metadata:
                raise KeyError(
                    'Metadata field "%s" not found for file %s' % (
                        fname, self.inputs.in_file))
            self._results[fname] = metadata.get(fname, Undefined)
        return runtime

class IntraModalMergeInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath(File(exists=True), mandatory=True,
                              desc='input files')
    hmc = traits.Bool(True, usedefault=True)
    zero_based_avg = traits.Bool(True, usedefault=True)
    to_ras = traits.Bool(True, usedefault=True)


class IntraModalMergeOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='merged image')
    out_avg = File(exists=True, desc='average image')
    out_mats = OutputMultiPath(File(exists=True), desc='output matrices')
    out_movpar = OutputMultiPath(File(exists=True), desc='output movement parameters')


class IntraModalMerge(SimpleInterface):
    input_spec = IntraModalMergeInputSpec
    output_spec = IntraModalMergeOutputSpec

    def _run_interface(self, runtime):
        in_files = self.inputs.in_files
        if not isinstance(in_files, list):
            in_files = [self.inputs.in_files]

        # Generate output average name early
        self._results['out_avg'] = fname_presuffix(self.inputs.in_files[0],
                                                   suffix='_avg', newpath=runtime.cwd)

        if self.inputs.to_ras:
            in_files = [reorient(inf, newpath=runtime.cwd)
                        for inf in in_files]

        if len(in_files) == 1:
            filenii = nb.load(in_files[0])
            filedata = filenii.get_data()

            # magnitude files can have an extra dimension empty
            if filedata.ndim == 5:
                sqdata = np.squeeze(filedata)
                if sqdata.ndim == 5:
                    raise RuntimeError('Input image (%s) is 5D' % in_files[0])
                else:
                    in_files = [fname_presuffix(in_files[0], suffix='_squeezed',
                                                newpath=runtime.cwd)]
                    nb.Nifti1Image(sqdata, filenii.affine,
                                   filenii.header).to_filename(in_files[0])

            if np.squeeze(nb.load(in_files[0]).get_data()).ndim < 4:
                self._results['out_file'] = in_files[0]
                self._results['out_avg'] = in_files[0]
                # TODO: generate identity out_mats and zero-filled out_movpar
                return runtime
            in_files = in_files[0]
        else:
            magmrg = fsl.Merge(dimension='t', in_files=self.inputs.in_files)
            in_files = magmrg.run().outputs.merged_file
        mcflirt = fsl.MCFLIRT(cost='normcorr', save_mats=True, save_plots=True,
                              ref_vol=0, in_file=in_files)
        mcres = mcflirt.run()
        self._results['out_mats'] = mcres.outputs.mat_file
        self._results['out_movpar'] = mcres.outputs.par_file
        self._results['out_file'] = mcres.outputs.out_file

        hmcnii = nb.load(mcres.outputs.out_file)
        hmcdat = hmcnii.get_data().mean(axis=3)
        if self.inputs.zero_based_avg:
            hmcdat -= hmcdat.min()

        nb.Nifti1Image(
            hmcdat, hmcnii.affine, hmcnii.header).to_filename(
            self._results['out_avg'])

        return runtime

class DerivativesDataSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    base_directory = traits.Directory(
        desc='Path to the base directory for storing data.')
    check_hdr = traits.Bool(True, usedefault=True, desc='fix headers of NIfTI outputs')
    compress = traits.Bool(desc="force compression (True) or uncompression (False)"
                                " of the output file (default: same as input)")
    desc = Str('', usedefault=True, desc='Label for description field')
    extra_values = traits.List(Str)
    in_file = InputMultiObject(File(exists=True), mandatory=True,
                               desc='the object to be saved')
    keep_dtype = traits.Bool(False, usedefault=True, desc='keep datatype suffix')
    meta_dict = traits.DictStrAny(desc='an input dictionary containing metadata')
    source_file = File(exists=False, mandatory=True, desc='the input func file')
    space = Str('', usedefault=True, desc='Label for space field')
    suffix = Str('', usedefault=True, desc='suffix appended to source_file')


class DerivativesDataSinkOutputSpec(TraitedSpec):
    out_file = OutputMultiObject(File(exists=True, desc='written file path'))
    out_meta = OutputMultiObject(File(exists=True, desc='written JSON sidecar path'))
    compression = OutputMultiObject(
        traits.Bool, desc='whether ``in_file`` was compressed/uncompressed '
                          'or `it was copied directly.')
    fixed_hdr = traits.List(traits.Bool, desc='whether derivative header was fixed')


class DerivativesDataSink(SimpleInterface):
    input_spec = DerivativesDataSinkInputSpec
    output_spec = DerivativesDataSinkOutputSpec
    out_path_base = "niworkflows"
    _always_run = True

    def __init__(self, allowed_entities=None, out_path_base=None, **inputs):
        self._allowed_entities = allowed_entities or []

        self._metadata = {}
        self._static_traits = self.input_spec.class_editable_traits() + self._allowed_entities
        for dynamic_input in set(inputs) - set(self._static_traits):
            self._metadata[dynamic_input] = inputs.pop(dynamic_input)

        super(DerivativesDataSink, self).__init__(**inputs)
        if self._allowed_entities:
            add_traits(self.inputs, self._allowed_entities)
            for k in set(self._allowed_entities).intersection(list(inputs.keys())):
                setattr(self.inputs, k, inputs[k])

        self._results['out_file'] = []
        if out_path_base:
            self.out_path_base = out_path_base

    def _run_interface(self, runtime):
        if isdefined(self.inputs.meta_dict):
            meta = self.inputs.meta_dict
            # inputs passed in construction take priority
            meta.update(self._metadata)
            self._metadata = meta

        src_fname, _ = _splitext(self.inputs.source_file)
        src_fname, dtype = src_fname.rsplit('_', 1)
        _, ext = _splitext(self.inputs.in_file[0])
        if self.inputs.compress is True and not ext.endswith('.gz'):
            ext += '.gz'
        elif self.inputs.compress is False and ext.endswith('.gz'):
            ext = ext[:-3]

        m = BIDS_NAME.search(src_fname)

        mod = Path(self.inputs.source_file).parent.name

        base_directory = runtime.cwd
        if isdefined(self.inputs.base_directory):
            base_directory = self.inputs.base_directory

        base_directory = Path(base_directory).resolve()
        out_path = base_directory / self.out_path_base / \
            '{subject_id}'.format(**m.groupdict())

        if m.groupdict().get('session_id') is not None:
            out_path = out_path / '{session_id}'.format(**m.groupdict())

        out_path = out_path / '{}'.format(mod)
        out_path.mkdir(exist_ok=True, parents=True)
        base_fname = str(out_path / src_fname)

        allowed_entities = {}
        for key in self._allowed_entities:
            value = getattr(self.inputs, key)
            if value is not None and isdefined(value):
                allowed_entities[key] = '_%s-%s' % (key, value)

        formatbase = '{bname}{space}{desc}' + ''.join(
            [allowed_entities.get(s, '') for s in self._allowed_entities])

        formatstr = formatbase + '{extra}{suffix}{dtype}{ext}'
        if len(self.inputs.in_file) > 1 and not isdefined(self.inputs.extra_values):
            formatstr = formatbase + '{suffix}{i:04d}{dtype}{ext}'

        space = '_space-{}'.format(self.inputs.space) if self.inputs.space else ''
        desc = '_desc-{}'.format(self.inputs.desc) if self.inputs.desc else ''
        suffix = '_{}'.format(self.inputs.suffix) if self.inputs.suffix else ''
        dtype = '' if not self.inputs.keep_dtype else ('_%s' % dtype)

        self._results['compression'] = []
        self._results['fixed_hdr'] = [False] * len(self.inputs.in_file)

        for i, fname in enumerate(self.inputs.in_file):
            extra = ''
            if isdefined(self.inputs.extra_values):
                extra = '_{}'.format(self.inputs.extra_values[i])
            out_file = formatstr.format(
                bname=base_fname,
                space=space,
                desc=desc,
                extra=extra,
                suffix=suffix,
                i=i,
                dtype=dtype,
                ext=ext,
            )
            self._results['out_file'].append(out_file)
            self._results['compression'].append(_copy_any(fname, out_file))

            is_nii = out_file.endswith('.nii') or out_file.endswith('.nii.gz')
            if self.inputs.check_hdr and is_nii:
                nii = nb.load(out_file)
                if not isinstance(nii, (nb.Nifti1Image, nb.Nifti2Image)):
                    # .dtseries.nii are CIfTI2, therefore skip check
                    return runtime
                hdr = nii.header.copy()
                curr_units = tuple([None if u == 'unknown' else u
                                    for u in hdr.get_xyzt_units()])
                curr_codes = (int(hdr['qform_code']), int(hdr['sform_code']))

                # Default to mm, use sec if data type is bold
                units = (curr_units[0] or 'mm', 'sec' if dtype == '_bold' else None)
                xcodes = (1, 1)  # Derivative in its original scanner space
                if self.inputs.space:
                    xcodes = (4, 4) if self.inputs.space in STANDARD_SPACES \
                        else (2, 2)

                if curr_codes != xcodes or curr_units != units:
                    self._results['fixed_hdr'][i] = True
                    hdr.set_qform(nii.affine, xcodes[0])
                    hdr.set_sform(nii.affine, xcodes[1])
                    hdr.set_xyzt_units(*units)

                    # Rewrite file with new header
                    nii.__class__(np.array(nii.dataobj), nii.affine, hdr).to_filename(
                        out_file)

        if len(self._results['out_file']) == 1:
            meta_fields = self.inputs.copyable_trait_names()
            self._metadata.update({
                k: getattr(self.inputs, k)
                for k in meta_fields if k not in self._static_traits})
            if self._metadata:
                sidecar = (Path(self._results['out_file'][0]).parent /
                           ('%s.json' % _splitext(self._results['out_file'][0])[0]))
                sidecar.write_text(dumps(self._metadata, sort_keys=True, indent=2))
                self._results['out_meta'] = str(sidecar)
        return runtime
