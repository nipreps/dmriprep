0.3.0 (October 13, 2020)
========================
A long overdue release including the milestones set for the 0.3.0 version in our roadmap.

* FIX: Revise vector tests broken when addressing other issues (#103)
* FIX: Minor refactor of DWI/brainmasks utilities and dtypes (#101)
* FIX: test pin to reports_bug branch (#59)
* FIX: circleci on_fail command (#61)
* ENH: An initial implementation of SD estimation. (#97)
* ENH: Minor refactor reorganizing base workflows, in prep for #97 (#110)
* ENH: Use new ``DerivativesDataSink`` from NiWorkflows 1.2.0 (#108)
* ENH: Port the new *anatomical fast-track* from *fMRIPrep* (#109)
* ENH: Data-driven *b0* identification tool (#107)
* ENH: Do not raise error in all instances of *b*-vecs/vals inconsistencies (#100)
* ENH: Update ``DiffusionGradientTable`` interface to support vector reorientation (#89)
* ENH: Update image utility output path behavior (#81)
* ENH: Adopt ``config`` module (#88)
* ENH: Added ``ds001771/sub-36`` dataset and FS derivatives (#67)
* DOC: Add nipreps developers and year to ``LICENSE`` file (#69)
* DOC: Roadmap documentation (#58)
* DOC: Document the fact that we are using popylar/GA for usage tracking (#63)
* MAINT: Remove the leftovers of AFQ in ``.afq/`` (#106)
* MAINT: Refactor the workflow to use *Nipype* iterables (#105)
* MAINT: Add ds001771 to the smoke-tests battery (#91)
* MAINT: Revisions after previous maintenance commit (#83) (#85)
* MAINT: Update dependencies (#83)


0.2.2 (January 15, 2020)
========================
A release to show the deployment process on the Sprint.

* ENH: b0 reference and skullstrip workflow (#50)
* FIX: Version on docker target of ``Makefile`` (#54)
* FIX/ENH: Remove sentry tracking and add popylar tracking. (#51)
* MAINT: Some small changes to the Dockerfile. (#53)
* ENH: Set up customized report specification (#34)
* MAINT: Use a local docker registry instead of load/save (#46)


0.2.1 (December 12, 2019)
=========================
A bugfix release to test that versioned documentation is working.

* FIX: Remove count of DWI scans according to ``task_id`` (#10)
* ENH: Vector representation and checking utilities (#26)
* ENH: Start running smoke tests on CircleCI (#31)
* ENH: Add config for CircleCI (#13)
* DOC: Build versioned docs and deploy them to gh-pages (#45)
* MAINT: Revise execution options in CircleCi (#33)
* MAINT: A minimal infrastructure for unit-tests, with some initial test files (#32)
* MAINT: Add a branch step to the contribution guidelines. (#21)
* MAINT: Add maintenance script to update the changelog, update CHANGES (#22)
* MAINT: Add a base of ``CONTRIBUTING.md`` guidelines (#14)
* MAINT: Fix typos and add Makefiles (#11)
* MAINT: Add TravisCI for code linting with ``flake8`` (#18)

0.2.0 (September 06, 2019)
==========================
A first attempt to roll out a release capable of running sMRIPrep for the anatomical processing.
This release will also serve to exercise the continuous deployment set-up.

0.1.1a0 (September 05, 2019)
============================
Testing Zenodo integration.

0.1.1 (September 05, 2019)
==========================
Tag to mark the start of a big refactor to adhere to fMRIPrep's principles.
dMRIPrep will bring the contents of this branch back in as a plugin.

0.1.0 (November 21, 2018)
=========================
* First release on GitHub.
