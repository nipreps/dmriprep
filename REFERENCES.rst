
Veraart et al. Denoising of diffusion MRI using random matrix theory (2016). Neuroimage 142:394-406
Kellner et al. Gibbs‐ringing artifact removal based on local subvoxel‐shifts (2016). Magn Reson Med 76:1574–1581

When using eddy and its QC tools, we ask you to please reference the papers describing the different aspects of the modelling and corrections. The (Andersson & Sotiropoulos, 2016) paper is the main eddy reference and should always be be cited when using eddy. The (Bastiani et al., 2019) paper is the main eddy QC reference and should always be be cited when using the QC tools. When using topup to estimate a fieldmap prior to running eddy one should also cite (Andersson et al., 2003). If you have used eddy to detect and replace outlier slices (by adding --repol to the eddy command line), please also cite (Andersson et al., 2016). If eddy was used to estimate and correct for intra-volume (slice-to-vol) movement by specifying --mporder, please also cite (Andersson et al., 2017). Finally, if you asked eddy to model how the susceptibility-induced distortions change as a consequence of subject movement (with the --estimate_move_by_susceptibility flag), please cite (Andersson et al., 2018).


REFERENCES

Jesper L.R. Andersson, Stefan Skare and John Ashburner. 2003. How to correct susceptibility distortions in spin-echo echo-planar images: application to diffusion tensor imaging. NeuroImage 20:870-888

Jesper L.R. Andersson and Stamatios N. Sotiropoulos. 2016. An integrated approach to correction for off-resonance effects and subject movement in diffusion MR imaging. NeuroImage 125:1063-1078

Jesper L.R. Andersson, Mark S. Graham, Eniko Zsoldos and Stamatios N. Sotiropoulos. 2016. Incorporating outlier detection and replacement into a non-parametric framework for movement and distortion correction of diffusion MR images. NeuroImage 141:556-572

Jesper L.R. Andersson, Mark S. Graham, Ivana Drobnjak, Hui Zhang, Nicola Filippini and Matteo Bastiani. 2017. Towards a comprehensive framework for movement and distortion correction of diffusion MR images: Within volume movement. NeuroImage 152:450-466

Jesper L.R. Andersson, Mark S. Graham, Ivana Drobnjak, Hui Zhang and Jon Campbell. 2018. Susceptibility-induced distortion that varies due to motion: Correction in diffusion MR without acquiring additional data. NeuroImage 171:277-295

Matteo Bastiani, Michiel Cottaar, Sean P. Fitzgibbon, Sana Suri, Fidel Alfaro-Almagro, Stamatios N. Sotiropoulos, Saad Jbabdi and Jesper L.R. Andersson. 2019. Automated quality control for within and between studies diffusion MRI data using a non-parametric framework for movement and distortion correction. NeuroImage 184:801-812
