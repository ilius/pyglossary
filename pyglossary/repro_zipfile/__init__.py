"""
Reproducible ZIP archive helper for PyGlossary writers.

Vendored ``ReproducibleZipFile`` normalizes timestamps, permissions, and
ordering so repeated builds yield byte-identical zip outputs.
"""

from .repro_zipfile import ReproducibleZipFile, __version__

__all__ = ["ReproducibleZipFile", "__version__"]
