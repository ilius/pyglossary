"""
PyGlossary package entry point.

Re-exports ``Glossary`` (the legacy import path) and ``__version__`` from
``core.VERSION`` for ``import pyglossary`` and setuptools metadata.
"""

from .core import VERSION
from .glossary import Glossary

__version__ = VERSION

__all__ = [
	"Glossary",
	"__version__",
]
