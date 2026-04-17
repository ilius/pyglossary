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

"""Session dataclass holding conversion parameters for the interactive cmd UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from pyglossary.config_type import ConfigType


__all__ = ["ConversionSession"]


@dataclass
class ConversionSession:
	"""
	Mutable state for a single interactive conversion (paths, formats, options).

	Used by ``UI`` (interactive cmd UI) to separate conversion
	data from UI wiring. Updated as the user picks files, formats, and plugin
	options; :meth:`get_run_kwargs` builds the keyword arguments for
	:meth:`pyglossary.ui.ui_cmd.UI.run`.
	"""

	inputFilename: str = ""
	outputFilename: str = ""
	inputFormat: str = ""
	outputFormat: str = ""
	readOptions: dict[str, Any] = field(default_factory=dict)
	writeOptions: dict[str, Any] = field(default_factory=dict)
	convertOptions: dict[str, Any] = field(default_factory=dict)
	glossarySetAttrs: dict[str, Any] = field(default_factory=dict)

	def get_run_kwargs(self, config: ConfigType) -> dict[str, Any]:
		"""
		Build kwargs for :meth:`pyglossary.ui.ui_cmd.UI.run` from this session.

		Merges ``config`` (global PyGlossary settings) with per-conversion fields
		stored on the session.
		"""
		return {
			"inputFilename": self.inputFilename,
			"outputFilename": self.outputFilename,
			"inputFormat": self.inputFormat,
			"outputFormat": self.outputFormat,
			"config": config,
			"readOptions": self.readOptions,
			"writeOptions": self.writeOptions,
			"convertOptions": self.convertOptions,
			"glossarySetAttrs": self.glossarySetAttrs,
		}
