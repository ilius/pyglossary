# -*- coding: utf-8 -*-
#
# Copyright © 2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

from typing import (
	Tuple,
	Dict,
	Optional,
	Callable,
)

from .option import Option
from .flags import (
	YesNoAlwaysNever,
	DEFAULT_NO,
)


class PluginProp(object):
	def __init__(self, plugin) -> None:
		self._p = plugin

	@property
	def pluginModule(self):
		return self._p

	@property
	def name(self) -> str:
		return self._p.format

	@property
	def description(self) -> str:
		return self._p.description

	@property
	def extensions(self) -> Tuple[str, ...]:
		return self._p.extensions

	@property
	def singleFile(self) -> bool:
		return self._p.singleFile

	@property
	def optionsProp(self) -> Dict[str, Option]:
		return getattr(self._p, "optionsProp", {})

	@property
	def depends(self) -> Dict[str, str]:
		return getattr(self._p, "depends", {})

	@property
	def supportsAlternates(self) -> bool:
		return self._p.supportsAlternates

	@property
	def sortOnWrite(self) -> YesNoAlwaysNever:
		return getattr(self._p, "sortOnWrite", DEFAULT_NO)
