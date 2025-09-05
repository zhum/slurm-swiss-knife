"""
Slurm CLI - A CLI tool for Slurm cluster management
with autocomplete functionality.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("slurm-cli")
except PackageNotFoundError:
    # Package is not installed (running from source without install)
    __version__ = "0.0.0-dev"

__author__ = "Sergey Zhumatiy"
__email__ = "szhumatiy@gmail.com"

__all__ = ["__version__", "__author__", "__email__"]
