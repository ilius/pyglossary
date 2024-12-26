# -*- coding: utf-8 -*-
#
# Copyright © 2008-2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
import os
import sys
from os.path import isdir, join
from typing import Any, NamedTuple

from . import core
from .core import (
	cacheDir,
	dataDir,
	pluginsDir,
	userPluginsDir,
)
from .glossary_utils import (
	Error,
	splitFilenameExt,
)
from .plugin_prop import PluginProp

__all__ = ["DetectedFormat", "PluginManager"]

log = logging.getLogger("pyglossary")


class DetectedFormat(NamedTuple):
	filename: str
	formatName: str
	compression: str


class PluginManager:
	plugins: dict[str, PluginProp] = {}
	pluginByExt: dict[str, PluginProp] = {}
	loadedModules: set[str] = set()

	formatsReadOptions: dict[str, dict[str, Any]] = {}
	formatsWriteOptions: dict[str, dict[str, Any]] = {}
	# for example formatsReadOptions[format][optName] gives you the default value

	readFormats: list[str] = []
	writeFormats: list[str] = []

	@classmethod
	def loadPluginsFromJson(cls: type[PluginManager], jsonPath: str) -> None:
		import json

		with open(jsonPath, encoding="utf-8") as _file:
			data = json.load(_file)

		for attrs in data:
			moduleName = attrs["module"]
			cls._loadPluginByDict(
				attrs=attrs,
				modulePath=join(pluginsDir, moduleName),
			)
			cls.loadedModules.add(moduleName)

	@classmethod
	def loadPlugins(
		cls: type[PluginManager],
		directory: str,
		skipDisabled: bool = True,
	) -> None:
		"""
		Load plugins from directory on startup.
		Skip importing plugin modules that are already loaded.
		"""
		import pkgutil

		# log.debug(f"Loading plugins from directory: {directory!r}")
		if not isdir(directory):
			log.critical(f"Invalid plugin directory: {directory!r}")
			return

		moduleNames = [
			moduleName
			for _, moduleName, _ in pkgutil.iter_modules([directory])
			if moduleName not in cls.loadedModules and moduleName != "formats_common"
		]
		moduleNames.sort()

		sys.path.append(directory)
		for moduleName in moduleNames:
			cls._loadPlugin(moduleName, skipDisabled=skipDisabled)
		sys.path.pop()

	@classmethod
	def _loadPluginByDict(
		cls: type[PluginManager],
		attrs: dict[str, Any],
		modulePath: str,
	) -> None:
		name = attrs["name"]

		extensions = attrs["extensions"]
		prop = PluginProp.fromDict(
			attrs=attrs,
			modulePath=modulePath,
		)
		if prop is None:
			return

		cls.plugins[name] = prop
		cls.loadedModules.add(attrs["module"])

		if not prop.enable:
			return

		for ext in extensions:
			if ext.lower() != ext:
				log.error(f"non-lowercase extension={ext!r} in {prop.name} plugin")
			cls.pluginByExt[ext.lstrip(".")] = prop
			cls.pluginByExt[ext] = prop

		if attrs["canRead"]:
			cls.formatsReadOptions[name] = attrs["readOptions"]
			cls.readFormats.append(name)

		if attrs["canWrite"]:
			cls.formatsWriteOptions[name] = attrs["writeOptions"]
			cls.writeFormats.append(name)

		if log.level <= core.TRACE:
			prop.module  # noqa: B018, to make sure importing works

	@classmethod
	def _loadPlugin(
		cls: type[PluginManager],
		moduleName: str,
		skipDisabled: bool = True,
	) -> None:
		log.debug(f"importing {moduleName} in loadPlugin")
		try:
			module = __import__(moduleName)
		except ModuleNotFoundError as e:
			log.warning(f"Module {e.name!r} not found, skipping plugin {moduleName!r}")
			return
		except Exception:
			log.exception(f"Error while importing plugin {moduleName}")
			return

		enable = getattr(module, "enable", False)
		if skipDisabled and not enable:
			# log.debug(f"Plugin disabled or not a module: {moduleName}")
			return

		prop = PluginProp.fromModule(module)

		name = prop.name

		cls.plugins[name] = prop
		cls.loadedModules.add(moduleName)

		if not enable:
			return

		for ext in prop.extensions:
			if ext.lower() != ext:
				log.error(f"non-lowercase extension={ext!r} in {moduleName} plugin")
			cls.pluginByExt[ext.lstrip(".")] = prop
			cls.pluginByExt[ext] = prop

		if prop.canRead:
			options = prop.getReadOptions()
			cls.formatsReadOptions[name] = options
			cls.readFormats.append(name)

		if prop.canWrite:
			options = prop.getWriteOptions()
			cls.formatsWriteOptions[name] = options
			cls.writeFormats.append(name)

	@classmethod
	def _findPlugin(
		cls: type[PluginManager],
		query: str,
	) -> PluginProp | None:
		"""Find plugin by name or extension."""
		plugin = cls.plugins.get(query)
		if plugin:
			return plugin
		plugin = cls.pluginByExt.get(query)
		if plugin:
			return plugin
		return None

	@classmethod
	def detectInputFormat(
		cls: type[PluginManager],
		filename: str,
		formatName: str = "",
	) -> DetectedFormat:
		filenameOrig = filename
		_, filename, ext, compression = splitFilenameExt(filename)

		plugin = None
		if formatName:
			plugin = cls.plugins.get(formatName)
			if plugin is None:
				raise Error(f"Invalid format {formatName!r}")
		else:
			plugin = cls.pluginByExt.get(ext)
			if not plugin:
				plugin = cls._findPlugin(filename)
				if not plugin:
					raise Error("Unable to detect input format!")

		if not plugin.canRead:
			raise Error(f"plugin {plugin.name} does not support reading")

		if compression in plugin.readCompressions:
			compression = ""
			filename = filenameOrig

		return DetectedFormat(filename, plugin.name, compression)

	@classmethod
	def _outputPluginByFormat(
		cls: type[PluginManager],
		formatName: str,
	) -> tuple[PluginProp | None, str]:
		if not formatName:
			return None, ""
		plugin = cls.plugins.get(formatName, None)
		if not plugin:
			return None, f"Invalid format {formatName}"
		if not plugin.canWrite:
			return None, f"plugin {plugin.name} does not support writing"
		return plugin, ""

	# C901		`detectOutputFormat` is too complex (16 > 13)
	# PLR0912	Too many branches (14 > 12)
	@classmethod
	def detectOutputFormat(  # noqa: PLR0912, PLR0913, C901
		cls: type[PluginManager],
		filename: str = "",
		formatName: str = "",
		inputFilename: str = "",
		addExt: bool = False,
	) -> DetectedFormat:
		from os.path import splitext

		plugin, err = cls._outputPluginByFormat(formatName)
		if err:
			raise Error(err)

		if not filename:
			# FIXME: not covered in tests
			if not inputFilename:
				raise Error(f"Invalid filename {filename!r}")  # type: ignore
			if not plugin:
				raise Error(
					"No filename nor format is given for output file",
				)  # type: ignore
			filename = splitext(inputFilename)[0] + plugin.ext
			return DetectedFormat(filename, plugin.name, "")

		filenameOrig = filename
		filenameNoExt, filename, ext, compression = splitFilenameExt(filename)

		if not plugin:
			plugin = cls.pluginByExt.get(ext)
			if not plugin:
				plugin = cls._findPlugin(filename)

		if not plugin:
			raise Error("Unable to detect output format!")  # type: ignore

		if not plugin.canWrite:
			raise Error(
				f"plugin {plugin.name} does not support writing",
			)  # type: ignore

		if compression in getattr(plugin.writerClass, "compressions", []):
			compression = ""
			filename = filenameOrig

		if addExt:
			if not filenameNoExt:
				if inputFilename:
					ext = plugin.ext
					filename = splitext(inputFilename)[0] + ext
				else:
					log.error("inputFilename is empty")
			if not ext and plugin.ext:
				filename += plugin.ext

		return DetectedFormat(filename, plugin.name, compression)

	@classmethod
	def init(
		cls: type[PluginManager],
		usePluginsJson: bool = True,
		skipDisabledPlugins: bool = True,
	) -> None:
		"""
		Initialize the glossary class (not an insatnce).
		Must be called only once, so make sure you put it in the right place.
		Probably in the top of your program's main function or module.
		"""
		cls.readFormats = []
		cls.writeFormats = []
		pluginsJsonPath = join(dataDir, "plugins-meta", "index.json")

		# even if usePluginsJson, we should still call loadPlugins to load
		# possible new plugins that are not in json file

		if usePluginsJson:
			cls.loadPluginsFromJson(pluginsJsonPath)

		cls.loadPlugins(pluginsDir, skipDisabled=skipDisabledPlugins)

		if isdir(userPluginsDir):
			cls.loadPlugins(userPluginsDir)

		os.makedirs(cacheDir, mode=0o700, exist_ok=True)
