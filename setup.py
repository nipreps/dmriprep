"""dMRIPrep's setup script."""
import sys
from setuptools import setup
import versioneer

if __name__ == "__main__":
    setupargs = {
        "version": versioneer.get_version(),
        "cmdclass": versioneer.get_cmdclass(),
    }
    if "bdist_wheel" in sys.argv:
        setupargs["setup_requires"] = ["setuptools >= 40.8", "wheel"]
    setup(**setupargs)
