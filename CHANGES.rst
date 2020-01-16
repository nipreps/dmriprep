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
