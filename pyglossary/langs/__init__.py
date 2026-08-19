"""
Language and locale helpers for PyGlossary.

Re-exports ``Lang`` and the global ``langDict`` mapping used to label glossary
source and target languages in UI and metadata.

This module is used in plugins.
"""

from .langs import Lang, langDict

__all__ = ["Lang", "langDict"]
