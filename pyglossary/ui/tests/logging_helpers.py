"""
Shared logging fixtures for ``pyglossary.ui`` unit tests.

Provides mock handlers and logger setup reused across UI test modules.
"""

from __future__ import annotations

import contextlib
import logging

__all__ = ["silence_pyglossary_log"]


@contextlib.contextmanager
def silence_pyglossary_log():
	"""Raise ``pyglossary`` logger level so normal messages are ignored."""
	logger = logging.getLogger("pyglossary")
	old_level = logger.level
	logger.setLevel(logging.CRITICAL + 1)
	try:
		yield
	finally:
		logger.setLevel(old_level)
