# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

from __future__ import annotations

__all__ = ["wx"]

try:
	import wx
except ImportError as err:  # pragma: no cover
	msg = "PyGlossary wx UI needs wxPython (install: pip install pyglossary[wx])."
	raise ImportError(msg) from err
