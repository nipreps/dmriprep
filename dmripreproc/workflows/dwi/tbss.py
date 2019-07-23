#!/usr/bin/env Python

# https://github.com/Conxz/BIT/blob/1ee7bbff345aba9d53b1349290f9fbdcbad1c3d0/bit/tbss_4steps_NKI.py

import os

from nipype.interfaces import io as nio, fsl, utility as niu
from nipype.pipeline import engine as pe
from nipype.workflows.dmri.fsl import tbss

def init_tbss_wf():

    def get_fa_list(subject_list):
        fa_list = []
        for subject_id in subject_list:
            fa_list.append(os.path.join(subject_id+'_FA'))
        return fa_list

    tbss_source = pe.Node(interface=nio.DataGrabber(outfiles=["fa_list"]), name="tbss_source")
    tbss_source.inputs.base_directory = os.path.abspath(sessdir)
    tbss_source.inputs.sort_filelist = True
    tbss_source.inputs.template = '%s.nii.gz'
    tbss_source.inputs.template_args = dict(fa_list=[[getFAList(subject_list)]])

    tbss1 = tbss.create_tbss_1_preproc(name="tbss1")

    tbss2 = tbss.create_tbss_2_reg(name="tbss2")
    tbss2.inputs.inputnode.target = fsl.Info.standard_image("FMRIB58_FA_1mm.nii.gz")

    tbss3 = tbss.create_tbss_3_postreg(name="tbss3", estimate_skeleton=True)

    tbss4 = tbss.create_tbss_4_prestats(name="tbss4")
