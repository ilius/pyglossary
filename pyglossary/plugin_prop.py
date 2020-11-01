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

from .option import Option
from .flags import (
	YesNoAlwaysNever,
	DEFAULT_NO,
)
import logging
from collections import OrderedDict as odict

log = logging.getLogger("pyglossary")


class PluginProp(object):
	def __init__(self, plugin) -> None:
		self._p = plugin
		self._Reader = None
		self._ReaderLoaded = False
		self._Writer = None
		self._WriterLoaded = False

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
	def extensions(self) -> "Tuple[str, ...]":
		return self._p.extensions

	@property
	def ext(self) -> str:
		extensions = self.extensions
		if extensions:
			return extensions[0]
		return ""

	@property
	def singleFile(self) -> bool:
		return self._p.singleFile

	@property
	def optionsProp(self) -> "Dict[str, Option]":
		return getattr(self._p, "optionsProp", {})

	@property
	def sortOnWrite(self) -> YesNoAlwaysNever:
		return getattr(self._p, "sortOnWrite", DEFAULT_NO)

	def _loadReaderClass(self) -> "Optional[Any]":
		cls = getattr(self._p, "Reader", None)
		if cls is None:
			return None
		for attr in (
			"__init__",
			"open",
			"close",
			"__len__",
			"__iter__",
		):
			if not hasattr(cls, attr):
				log.error(
					f"Invalid Reader class in {self.name!r} plugin"
					f", no {attr!r} method"
				)
				self._p.Reader = None
				return None

		if hasattr(cls, "depends"):
			if not isinstance(cls.depends, dict):
				log.error(
					f"invalid depends={cls.depends}"
					f" in {self.name!r}.Reader class"
				)
		else:
			cls.depends = {}

		return cls

	@property
	def readerClass(self) -> "Optional[Any]":
		if self._ReaderLoaded:
			return self._Reader
		cls = self._loadReaderClass()
		self._Reader = cls
		self._ReaderLoaded = True
		return cls

	def _loadWriterClass(self) -> "Optional[Any]":
		cls = getattr(self._p, "Writer", None)
		if cls is None:
			return None
		for attr in (
			"__init__",
			"open",
			"write",
			"finish",
		):
			if not hasattr(cls, attr):
				log.error(
					f"Invalid Writer class in {self.name!r} plugin"
					f", no {attr!r} method"
				)
				self._p.Writer = None
				return None

		if hasattr(cls, "depends"):
			if not isinstance(cls.depends, dict):
				log.error(
					f"invalid depends={cls.depends}"
					f" in {self.name!r}.Writer class"
				)
		else:
			cls.depends = {}

		return cls

	@property
	def writerClass(self) -> "Optional[Any]":
		if self._WriterLoaded:
			return self._Writer
		cls = self._loadWriterClass()
		self._Writer = cls
		self._WriterLoaded = True
		return cls

	@property
	def canRead(self) -> bool:
		return self.readerClass is not None

	@property
	def canWrite(self) -> bool:
		return self.writerClass is not None

	def getReadOptions(self):
		return self.getOptionsFromClass(self.readerClass)

	def getWriteOptions(self):
		return self.getOptionsFromClass(self.writerClass)

	def getOptionsFromClass(self, rwclass):
		optionsProp = self.optionsProp
		options = odict()
		for attrName in dir(rwclass):
			if not attrName.startswith("_"):
				continue
			if attrName.startswith("__"):
				continue
			name = attrName[1:]
			default = getattr(rwclass, attrName)
			if name not in optionsProp:
				if not callable(default):
					log.warning(
						f"format={self.name}, attrName={attrName}, type={type(default)}"
					)
				continue
			prop = optionsProp[name]
			if prop.disabled:
				log.trace(f"skipping disabled option {name} in {self.name} plugin")
				continue
			if not prop.validate(default):
				log.warning(
					"invalid default value for option: "
					f"{name} = {default!r} in plugin {self.name}"
				)
			options[name] = default

		return options

	def getReadExtraOptions(self):
		return self.__class__.getExtraOptions(self.readerClass.open, self.name)

	def getWriteExtraOptions(self):
		return self.__class__.getExtraOptions(self.writerClass.write, self.name)

	@classmethod
	def getExtraOptions(cls, func, format):
		import inspect
		extraOptNames = []
		for name, param in inspect.signature(func).parameters.items():
			if param.default is not inspect._empty:
				extraOptNames.append(name)
				continue
			if name not in ("self", "filename", "dirname"):
				extraOptNames.append(name)
		if extraOptNames:
			log.debug(f"{format}: extraOptNames = {extraOptNames}")
		return extraOptNames
