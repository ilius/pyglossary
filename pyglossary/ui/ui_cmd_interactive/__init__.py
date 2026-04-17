# -*- coding: utf-8 -*-
# mypy: ignore-errors
#
# Copyright © 2025 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.
"""
Interactive command-line UI for PyGlossary (``--ui=cmd`` interactive mode).

Requires `prompt_toolkit` (``pip install prompt_toolkit``). Import :class:`UI`
from this package and call :meth:`UI.run` with the same keyword arguments as
the non-interactive command-line UI; the user is then guided through paths,
formats, options, and conversion in a prompt-driven session.
"""

from __future__ import annotations

from .ui import UI

__all__ = ["UI"]
