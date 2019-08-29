Susceptibility Distortion Correction (SDC)
------------------------------------------

Introduction
~~~~~~~~~~~~

Correction Methods
~~~~~~~~~~~~~~~~~~

  1. topup

  2. fieldmap

  3. phasediff

  4. phase1/phase2

  5. nonlinear registration

  6. synthetic b0
  
  The synb0 method is based off of this `paper <https://www.sciencedirect.com/science/article/abs/pii/S0730725X18306179/>`_. It offers an alternative method of SDC by using deep learning on an anatomical image (T1).
  
  You can use it in this pipeline by generating the synb0s for the subject(s) and passing the bids-like directory containing them to the --synb0_dir parameter. To find out how to generate the synb0s, you can visit our `forked repo <https://github.com/TIGRLab/Synb0-DISCO>`_.
  
  Once you have a directory of synb0s (recommended to place as derivatives of bids folder, ex. bids/derivatives/synb0/sub-XX), then you are ready to run the pipeline using them! Just run dmripreproc as you usually would, with bids_dir and output_dir, but now add "--synb0_dir <your_synb0_directory>" to your command. 
    
  The synb0 acqp for topup and eddy will be automatically generated in the pipeline in the following format:
  
  0 -1 0 <total_readout_time>
  
  0 1 0 0
  
  If you want to overwrite the total_readout_time with one of your own, simply add "--total_readout <new_trt_time>" to your command.
