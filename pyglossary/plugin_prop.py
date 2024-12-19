# -*- coding: utf-8 -*-
#
# Copyright © 2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import pathlib
	from typing import Any

	from .flags import StrWithDesc

from . import core
from .flags import (
	DEFAULT_NO,
	YesNoAlwaysNever,
	flagsByName,
)
from .option import Option, optionFromDict

__all__ = ["PluginProp"]

log = logging.getLogger("pyglossary")


def optionsPropFromDict(
	optionsPropDict: dict[str, Any],
) -> dict[str, Option]:
	props: dict[str, Option] = {}
	for name, propDict in optionsPropDict.items():
		try:
			prop = optionFromDict(propDict)
		except Exception:
			log.exception(f"{name=}, {propDict=}\n")
			continue
		props[name] = prop
	return props


def sortOnWriteFromStr(sortOnWriteStr: str | None) -> StrWithDesc:
	if sortOnWriteStr is None:
		return DEFAULT_NO
	return flagsByName[sortOnWriteStr]


class PluginCheckError(Exception):
	pass


class PluginProp:  # noqa: PLR0904
	__slots__ = [
		"_Reader",
		"_ReaderLoaded",
		"_Writer",
		"_WriterLoaded",
		"_canRead",
		"_canWrite",
		"_description",
		"_enable",
		"_extensionCreate",
		"_extensions",
		"_lname",
		"_mod",
		"_moduleName",
		"_modulePath",
		"_name",
		"_optionsProp",
		"_readCompressions",
		"_readDepends",
		"_readOptions",
		"_singleFile",
		"_sortKeyName",
		"_sortOnWrite",
		"_writeDepends",
		"_writeOptions",
	]

	def __init__(self) -> None:
		self._mod: Any
		self._Reader: Any
		self._ReaderLoaded: bool
		self._Writer: Any
		self._WriterLoaded: bool

		self._moduleName: str
		self._modulePath: str
		self._enable: bool
		self._lname: str
		self._name: str
		self._description: str
		self._extensions: list[str]
		self._extensionCreate: str
		self._singleFile: bool
		self._optionsProp: dict[str, Option]
		self._sortOnWrite: YesNoAlwaysNever
		self._sortKeyName: str | None
		self._canRead: bool
		self._canWrite: bool
		self._readOptions: dict[str, Any]
		self._writeOptions: dict[str, Any]
		self._readCompressions: list[str]
		self._readDepends: dict[str, str]
		self._writeDepends: dict[str, str]

	@classmethod
	def fromDict(
		cls: type,
		attrs: dict[str, Any],
		modulePath: str,
	) -> None:
		self = cls()
		self._mod = None
		self._Reader = None
		self._ReaderLoaded = False
		self._Writer = None
		self._WriterLoaded = False

		self._moduleName = attrs["module"]
		self._modulePath = modulePath
		self._enable = attrs.get("enable", True)
		self._lname = attrs["lname"]
		self._name = attrs["name"]
		self._description = attrs["description"]
		self._extensions = attrs["extensions"]
		self._extensionCreate = attrs.get("extensionCreate", "")
		self._singleFile = attrs["singleFile"]
		self._optionsProp = optionsPropFromDict(attrs["optionsProp"])
		self._sortOnWrite = sortOnWriteFromStr(attrs.get("sortOnWrite"))
		self._sortKeyName = attrs.get("sortKeyName")
		self._canRead = attrs["canRead"]
		self._canWrite = attrs["canWrite"]
		self._readOptions = attrs.get("readOptions", {})
		self._writeOptions = attrs.get("writeOptions", {})
		self._readCompressions = attrs.get("readCompressions", [])
		self._readDepends = attrs.get("readDepends", {})
		self._writeDepends = attrs.get("writeDepends", {})

		return self

	@classmethod
	def fromModule(cls: type, mod: Any) -> PluginProp:  # noqa: ANN401
		self = cls()
		self._mod = mod
		self._Reader = None
		self._ReaderLoaded = False
		self._Writer = None
		self._WriterLoaded = False

		self._moduleName = mod.__name__
		self._modulePath = mod.__file__
		if self._modulePath.endswith("__init__.py"):
			self._modulePath = self._modulePath[: -len("/__init__.py")]
		elif self._modulePath.endswith(".py"):
			self._modulePath = self._modulePath[:-3]

		self._enable = getattr(mod, "enable", True)
		self._lname = mod.lname
		if hasattr(mod, "name"):
			self._name = mod.name
		else:
			self._name = mod.format
			warnings.warn(
				"`format` variable in plugin is deprecated, rename it to `name`",
				category=DeprecationWarning,
				stacklevel=2,
			)
		self._description = mod.description
		self._extensions = list(mod.extensions)
		self._extensionCreate = getattr(mod, "extensionCreate", "")
		self._singleFile = getattr(mod, "singleFile", False)
		self._optionsProp = getattr(mod, "optionsProp", {})
		self._sortOnWrite = getattr(mod, "sortOnWrite", DEFAULT_NO)
		self._sortKeyName = getattr(mod, "sortKeyName", None)
		self._canRead = hasattr(mod, "Reader")
		self._canWrite = hasattr(mod, "Writer")
		self._readOptions = None
		self._writeOptions = None
		self._readCompressions = None
		self._readDepends = None
		self._writeDepends = None

		if core.isDebug():
			self.checkModule(mod)

		return self

	@property
	def enable(self) -> bool:
		return self._enable

	@property
	def module(self) -> Any:  # noqa: ANN401
		if self._mod is not None:
			return self._mod
		moduleName = self._moduleName
		log.debug(f"importing {moduleName} in DictPluginProp")
		try:
			mod = __import__(
				f"pyglossary.plugins.{moduleName}",
				fromlist=moduleName,
			)
		except ModuleNotFoundError as e:
			log.warning(
				f"Module {e.name!r} not found in {self._modulePath}"
				f", skipping plugin {moduleName!r}",
			)
			return None
		except Exception:
			log.exception(f"Error while importing plugin {moduleName}")
			return None

		# self._mod = _mod
		if core.isDebug():
			self.checkModule(mod)

		return mod

	@property
	def lname(self) -> str:
		return self._lname

	@property
	def name(self) -> str:
		return self._name

	@property
	def description(self) -> str:
		return self._description

	@property
	def extensions(self) -> list[str]:
		return self._extensions

	@property
	def ext(self) -> str:
		extensions = self.extensions
		if extensions:
			return extensions[0]
		return ""

	@property
	def extensionCreate(self) -> str:
		return self._extensionCreate

	@property
	def singleFile(self) -> bool:
		return self._singleFile

	@property
	def optionsProp(self) -> dict[str, Option]:
		return self._optionsProp

	@property
	def sortOnWrite(self) -> YesNoAlwaysNever:
		return self._sortOnWrite

	@property
	def sortKeyName(self) -> str | None:
		return self._sortKeyName

	@property
	def path(self) -> pathlib.Path:
		from pathlib import Path

		return Path(self._modulePath)

	@property
	def readerClass(self) -> type | None:
		if self._ReaderLoaded:
			return self._Reader
		cls = getattr(self.module, "Reader", None)
		self._Reader = cls
		self._ReaderLoaded = True
		if cls is not None and core.isDebug():
			self.checkReaderClass()
		return cls

	@property
	def writerClass(self) -> type | None:
		if self._WriterLoaded:
			return self._Writer
		cls = getattr(self.module, "Writer", None)
		self._Writer = cls
		self._WriterLoaded = True
		if cls is not None and core.isDebug():
			self.checkWriterClass()
		return cls

	@property
	def canRead(self) -> bool:
		return self._canRead

	@property
	def canWrite(self) -> bool:
		return self._canWrite

	@staticmethod
	def _getOptionAttrNamesFromClass(rwclass: type) -> list[str]:
		nameList = []

		for cls in (*rwclass.__bases__, rwclass):
			for _name in cls.__dict__:
				if not _name.startswith("_") or _name.startswith("__"):
					# and _name not in ("_open",)
					continue
				nameList.append(_name)

		# rwclass.__dict__ does not include attributes of parent/base class
		# and dir(rwclass) is sorted by attribute name alphabetically
		# using rwclass.__bases__ solves the problem

		return nameList

	def _getOptionsFromClass(self, rwclass: type | None) -> dict[str, Any]:
		if rwclass is None:
			return {}

		optionsProp = self.optionsProp
		options: dict[str, Any] = {}

		for attrName in self._getOptionAttrNamesFromClass(rwclass):
			name = attrName[1:]
			default = getattr(rwclass, attrName)
			if name not in optionsProp:
				continue
			prop = optionsProp[name]
			if prop.disabled:
				core.trace(
					log,
					f"skipping disabled option {name} in {self.name} plugin",
				)
				continue
			if not prop.validate(default):
				log.warning(
					"invalid default value for option: "
					f"{name} = {default!r} in plugin {self.name}",
				)
			options[name] = default

		return options

	def getReadOptions(self) -> dict[str, Any]:
		if self._readOptions is None:
			self._readOptions = self._getOptionsFromClass(self.readerClass)
		return self._readOptions

	def getWriteOptions(self) -> dict[str, Any]:
		if self._writeOptions is None:
			self._writeOptions = self._getOptionsFromClass(self.writerClass)
		return self._writeOptions

	@property
	def readCompressions(self) -> list[str]:
		if self._readCompressions is None:
			self._readCompressions = getattr(self.readerClass, "compressions", [])
		return self._readCompressions

	@property
	def readDepends(self) -> dict[str, str]:
		if self._readDepends is None:
			self._readDepends = getattr(self.readerClass, "depends", {})
		return self._readDepends

	@property
	def writeDepends(self) -> dict[str, str]:
		if self._writeDepends is None:
			self._writeDepends = getattr(self.writerClass, "depends", {})
		return self._writeDepends

	def checkModule(self, module: Any) -> None:  # noqa: ANN401
		name = self.name

		if hasattr(module, "write"):
			log.error(
				f"plugin {name!r} has write function, must migrate to Writer class",
			)

		extensions = module.extensions
		if not isinstance(extensions, tuple):
			msg = f"{name} plugin: extensions must be tuple"
			if isinstance(extensions, list):
				extensions = tuple(extensions)
				log.error(msg)
			else:
				raise TypeError(msg)

		if not isinstance(self.readDepends, dict):
			log.error(
				f"invalid depends={self.readDepends} in {self.name!r}.Reader class",
			)

		if not isinstance(self.writeDepends, dict):
			log.error(
				f"invalid depends={self.writeDepends}"
				f" in {self.name!r}.Reader class",
			)

		for name, opt in self.optionsProp.items():
			if name.lower() != name:
				suggestName = "".join(
					"_" + x.lower() if x.isupper() else x for x in name
				)
				log.debug(
					f"{self.name}: please rename option {name} to {suggestName}",
				)
			if not opt.comment:
				log.debug(
					f"{self.name}: please add comment for option {name}",
				)

	valid__all__ = [
		"enable",
		"lname",
		"name",
		"description",
		"extensions",
		"extensionCreate",
		"singleFile",
		"kind",
		"wiki",
		"website",
		"optionsProp",
		"Reader",
		"Writer",
	]

	# only run this on CI to do extra validation
	def checkModuleMore(self, module: Any) -> None:
		name = self.name
		if not hasattr(module, "__all__"):
			raise PluginCheckError(f"Please add __all__ to plugin {name!r}")
		all_ = module.__all__
		for attr in all_:
			if not hasattr(module, attr):
				raise PluginCheckError(
					f"Undefined name {attr!r} in __all__ in plugin {name!r}"
					f": {module.__file__}",
				)
			if attr not in self.valid__all__:
				raise PluginCheckError(
					f"Unnecessary name {attr!r} in __all__ in plugin {name!r}"
					f": {module.__file__}",
				)

	def checkReaderClass(self) -> bool:
		cls = self._Reader
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
					f", no {attr!r} method",
				)
				self._Reader = None
				return False

		return True

	def checkWriterClass(self) -> bool:
		cls = self._Writer
		for attr in (
			"__init__",
			"open",
			"write",
			"finish",
		):
			if not hasattr(cls, attr):
				log.error(
					f"Invalid Writer class in {self.name!r} plugin"
					f", no {attr!r} method",
				)
				self._Writer = None
				return False

		return True

	# def _getReadExtraOptions(self) -> list[str]:  # noqa: F811
	# 	cls = self.readerClass
	# 	if cls is None:
	# 		return []
	# 	return self.__class__.getExtraOptionsFromFunc(cls.open, self.name)

	# def _getWriteExtraOptions(self) -> list[str]:  # noqa: F811
	# 	cls = self.writerClass
	# 	if cls is None:
	# 		return []
	# 	return self.__class__.getExtraOptionsFromFunc(cls.write, self.name)

	# @classmethod
	# def getExtraOptionsFromFunc(
	# 	cls: type,
	# 	func: Callable,
	# 	format: str,
	# ) -> list[str]:
	# 	import inspect

	# 	extraOptNames = []
	# 	for name, param in inspect.signature(func).parameters.items():
	# 		if name == "self":
	# 			continue
	# 		if str(param.default) != "<class 'inspect._empty'>":
	# 			extraOptNames.append(name)
	# 			continue
	# 		if name not in {"filename", "dirname"}:
	# 			extraOptNames.append(name)
	# 	if extraOptNames:
	# 		log.warning(f"{format}: {extraOptNames = }")
	# 	return extraOptNames
