"""Vendored ``wcwidth`` package for terminal column alignment.

Python port of Markus Kuhn's Unicode width tables used by interactive CLI
prompts to pad and wrap text correctly in fixed-width terminals.
"""
from.wcwidth import ZERO_WIDTH,WIDE_EASTASIAN,VS16_NARROW_TO_WIDE,wcwidth,wcswidth,_bisearch,list_versions,_wcmatch_version,_wcversion_value
__all__='wcwidth','wcswidth','list_versions'
__version__='0.2.14'