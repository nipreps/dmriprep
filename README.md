[![Known Vulnerabilities](https://snyk.io/test/github/nipy/dmriprep/badge.svg)](https://snyk.io/test/github/nipy/dmriprep)
[![Documentation Status](https://readthedocs.org/projects/dmriprep/badge/?version=latest)](httpsL//dmriprep.readthredocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/nipy/dmriprep.png?branch=master)](https://travis-ci.org/nipy/dmriprep)
[![Coverage Status](https://coveralls.io/repos/github/nipy/dmriprep/badge.svg?branch=master)](https://coveralls.io/github/nipy/dmriprep?branch=master)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

# dmriprep

Preprocessing of neuroimaging data in preparation for AFQ analysis

* Free software: BSD license
* Documentation: https://dmriprep.readthedocs.io.

## Preparing your data

You should have raw data organized in the BIDS format. Also, you should have run Freesurfer and the results should be in a derivatives/ folder:

    BIDS_input_dir
    ├── sub-01
    │   ├── dwi
    │   │   ├── sub-01_ses-01_dwi.nii.gz
    │   │   ├── sub-01_ses-01_dwi.bval
    │   │   ├── sub-01_ses-01_dwi.bvec
    │   ├── fmap
    │   │   ├── sub-01_ses-01_acq-dwi_dir-AP_epi.nii.gz
    │   │   ├── sub-01_ses-01_acq-dwi_dir-PA_epi.nii.gz
    │   │   ├── sub-01_ses-01_acq-dwi_dir-AP_epi.json
    │   │   ├── sub-01_ses-01_acq-dwi_dir-PA_epi.json
    ├── derivatives
    │   ├── sub-01
    │   │   ├── freesurfer

## Quickstart

```bash
git clone https://github.com/nipy/dmriprep
cd dmriprep
python setup.py install

dmriprep $BIDS_INPUT_DIR $OUTPUT_DIR --participant-label 01
```

```bash
git clone https://github.com/nipy/dmriprep
cd dmriprep
make docker

# If you don't want to log into the docker image:

docker run -ti -v $BIDS_INPUT_DIR:/inputs -v $OUTPUT_DIR:/outputs dmriprep:prod dmriprep /inputs /outputs

# If you want to log into the image:

docker run -ti -v $BIDS_INPUT_DIR:/inputs -v $OUTPUT_DIR:/outputs dmriprep:prod 

# Run this inside the docker image:
dmriprep /inputs /outpus --participant-label 01
```

## Features

* TODO

## Contributing

We love contributions! dmriprep is open source, built on open source,
and we'd love to have you hang out in our community.

We have developed some [guidelines](CONTRIBUTING.rst) for contributing to
dmriprep.

**Imposter syndrome disclaimer**: We want your help. No, really.

There may be a little voice inside your head that is telling you that
you're not ready to be an open source contributor; that your skills
aren't nearly good enough to contribute. What could you possibly offer a
project like this one?

We assure you - the little voice in your head is wrong. If you can
write code at all, you can contribute code to open source. Contributing
to open source projects is a fantastic way to advance one's coding
skills. Writing perfect code isn't the measure of a good developer (that
would disqualify all of us!); it's trying to create something, making
mistakes, and learning from those mistakes. That's how we all improve,
and we are happy to help others learn.

Being an open source contributor doesn't just mean writing code, either.
You can help out by writing documentation, tests, or even giving
feedback about the project (and yes - that includes giving feedback
about the contribution process). Some of these contributions may be the
most valuable to the project as a whole, because you're coming to the
project with fresh eyes, so you can see the errors and assumptions that
seasoned contributors have glossed over.

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [`audreyr/cookiecutter-pypackage`](https://github.com/audreyr/cookiecutter-pypackage) project template.

The imposter syndrome disclaimer was originally written by
[Adrienne Lowe](https://github.com/adriennefriend) for a [PyCon
talk](https://www.youtube.com/watch?v=6Uj746j9Heo), and was
adapted based on its use in the README file for the [MetPy
project](https://github.com/Unidata/MetPy).

