# -*- coding: utf-8 -*-

"""
Head motion, eddy current distortion and EPI distortion correction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: init_dwi_eddy_wf

"""

from nipype.pipeline import engine as pe
from nipype.interfaces import fsl, utility as niu
from numba import cuda


def init_dwi_eddy_wf(omp_nthreads):

    wf = pe.Workflow(name="dwi_eddy_wf")

    inputnode = pe.Node(niu.IdentityInterface(fields=["dwi_file",
                                                      "bvec_file",
                                                      "bval_file",
                                                      "mask_file",
                                                      "acqp",
                                                      "index"]),
                       name="inputnode")

    outputnode = pe.Node(niu.IdentityInterface(fields=["out_file", "out_bvec"]),
                         name="outputnode")

    ecc = pe.Node(
        fsl.Eddy(num_threads=1, repol=True, cnr_maps=True, residuals=True),
        name="fsl_eddy",
    )

    if omp_nthreads:
        ecc.inputs.num_threads = omp_nthreads

    # this doesn't work well
    # recognizes that a computer is cuda capable but failed if cuda isn't loaded
    try:
        if cuda.gpus:
            ecc.inputs.use_cuda = True
    except:
        ecc.inputs.use_cuda = False

    wf.connect([
        (inputnode, ecc, [("dwi_file", "in_file"),
                          ("bval_file", "in_bval"),
                          ("bvec_file", "in_bvec"),
                          ("acqp", "in_acqp"),
                          ("index", "in_index"),
                          ("mask_file", "in_mask")]),
        (ecc, outputnode, [("out_corrected", "out_file"),
                           ("out_rotated_bvecs", "out_bvec")])
        ])

    return wf
