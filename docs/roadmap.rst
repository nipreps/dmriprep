.. include:: links.rst

--------------------
Development road map
--------------------

This road-map serves as a guide for developers as well as a way for us to
communicate to users and other stake-holders aboout the expectations they should
have about the current functionality of the software and future developments.


Version 0.3
-----------
This version should be considered an early alpha of the software, but will
contain a full pipeline of processing from a raw BIDS dataset to analyzable data.

At this point, the processing pipeline will include the following steps:

#. Head motion correction.
#. Eddy current correction.
#. Susceptibility distortion correction.
#. Gibbs ringing (using DIPY's image-based implementation).
#. Identification of outliers.
#. Registration between dMRI and T1w image.




