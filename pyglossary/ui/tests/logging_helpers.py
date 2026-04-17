# -*- coding: utf-8 -*-
"""Shared helpers for ``pyglossary.ui`` unit tests."""

from __future__ import annotations

import contextlib
import logging


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
