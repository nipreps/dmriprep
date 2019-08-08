.. highlight:: shell

============
Contributing
============

We love contributions! dmriprep is open source, built on open source,
and we'd love to have you hang out in our community.

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

Installing a development version of dmriprep
--------------------------------------------

First, you can install a development version of dmriprep by cloning this repository
and then typing::

    $ pip install -e .[dev]

Activate the pre-commit formatting hook by typing::

    $ pre-commit install

Before committing your work, you can check for formatting issues or error by typing::

    $ make lint
    $ make test

Types of Contributions
----------------------

You can contribute in many ways:

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/nipy/dmriprep/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

dmriprep could always use more documentation, whether as part of the
official dmriprep docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/nipy/dmriprep/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `dmriprep` for local development.

1. Fork the `dmriprep` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/dmriprep.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv dmriprep
    $ cd dmriprep/
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 dmriprep tests
    $ python setup.py test or py.test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 3.5, 3.6 and 3.7, and for PyPy. Check
   https://travis-ci.org/tigrlab/dmriprep/pull_requests
   and make sure that the tests pass for all supported Python versions.

When opening a pull request, please use one of the following prefixes:

* **[ENH]** for enhancements
* **[FIX]** for bug fixes
* **[TST]** for new or updated tests
* **[DOC]** for new or updated documentation
* **[STY]** for stylistic changes
* **[REF]** for refactoring existing code

Tips
----

To run a subset of tests::

$ py.test tests.test_dmriprep


Deploying
---------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).
Then run::

$ bumpversion patch # possible: major / minor / patch
$ git push
$ git push --tags

Travis will then deploy to PyPI if tests pass.

The imposter syndrome disclaimer was originally written by
`Adrienne Lowe <https://github.com/adriennefriend>`_ for a `PyCon talk <https://www.youtube.com/watch?v=6Uj746j9Heo>`_, and was
adapted based on its use in the README file for the `MetPy project <https://github.com/Unidata/MetPy>`_.
