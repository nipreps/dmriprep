"""Test util workflows."""
import pytest

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from nipype.pipeline import engine as pe

from dmriprep.workflows.dwi.util import init_dwi_reference_wf
from dmriprep.interfaces.vectors import CheckGradientTable


@pytest.mark.parametrize('dataset', [
    'THP002'
])
def test_util(bids_layouts, tmpdir, output_path, dataset, workdir):
    """Test creation of the workflow."""
    tmpdir.chdir()

    data = bids_layouts[dataset]
    wf = Workflow(name='util_%s' % dataset)
    util_wf = init_dwi_reference_wf(omp_nthreads=1)

    dwi_file = data.get(
        datatype='dwi',
        return_type='file',
        extension=['.nii', '.nii.gz'])

    bvec_file = data.get_bvec(dwi_file)
    bval_file = data.get_bval(dwi_file)

    gradient_table = pe.Node(CheckGradientTable(
        dwi_file=dwi_file,
        in_bvec=bvec_file,
        in_bval=bval_file), name='gradient_table')

    util_wf.inputs.inputnode.dwi_file = dwi_file

    wf.connect([
        gradient_table, util_wf, [('b0_ixs', 'b0_ixs')],
    ])

    if workdir:
        wf.base_dir = str(workdir)

    wf.run()
