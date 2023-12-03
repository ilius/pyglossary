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

import logging
import os
import sys
from collections import namedtuple
from os.path import isdir, join
from typing import Any

from . import core
from .core import (
	cacheDir,
	dataDir,
	pluginsDir,
	userPluginsDir,
)
from .glossary_utils import (
	splitFilenameExt,
)
from .plugin_prop import PluginProp

log = logging.getLogger("pyglossary")

DetectedFormat = namedtuple(
	"DetectedFormat", [
		"filename",  # str
		"formatName",  # str
		"compression",  # str
	],
)


class PluginManager:
	plugins: "dict[str, PluginProp]" = {}
	pluginByExt: "dict[str, PluginProp]" = {}
	loadedModules: "set[str]" = set()

	formatsReadOptions: "dict[str, dict[str, Any]]" = {}
	formatsWriteOptions: "dict[str, dict[str, Any]]" = {}
	# for example formatsReadOptions[format][optName] gives you the default value

	readFormats: "list[str]" = []
	writeFormats: "list[str]" = []

	@classmethod
	def loadPluginsFromJson(cls: "type[PluginManager]", jsonPath: str) -> None:
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
		cls: "type[PluginManager]",
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
			if moduleName not in cls.loadedModules and
			moduleName != "formats_common"
		]
		moduleNames.sort()

		sys.path.append(directory)
		for moduleName in moduleNames:
			cls._loadPlugin(moduleName, skipDisabled=skipDisabled)
		sys.path.pop()

	@classmethod
	def _loadPluginByDict(
		cls: "type[PluginManager]",
		attrs: "dict[str, Any]",
		modulePath: str,
	) -> None:
		format = attrs["name"]

		extensions = attrs["extensions"]
		prop = PluginProp.fromDict(
			attrs=attrs,
			modulePath=modulePath,
		)
		if prop is None:
			return

		cls.plugins[format] = prop
		cls.loadedModules.add(attrs["module"])

		if not prop.enable:
			return

		for ext in extensions:
			if ext.lower() != ext:
				log.error(f"non-lowercase extension={ext!r} in {prop.name} plugin")
			cls.pluginByExt[ext.lstrip(".")] = prop
			cls.pluginByExt[ext] = prop

		if attrs["canRead"]:
			cls.formatsReadOptions[format] = attrs["readOptions"]
			cls.readFormats.append(format)

		if attrs["canWrite"]:
			cls.formatsWriteOptions[format] = attrs["writeOptions"]
			cls.writeFormats.append(format)

		if log.level <= core.TRACE:
			prop.module  # noqa: B018, to make sure importing works

	@classmethod
	def _loadPlugin(
		cls: "type[PluginManager]",
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

		name = module.format

		prop = PluginProp.fromModule(module)

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
		cls: "type[PluginManager]",
		query: str,
	) -> "PluginProp | None":
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
		cls: "type[PluginManager]",
		filename: str,
		format: str = "",
		quiet: bool = False,
	) -> "DetectedFormat | None":
		def error(msg: str) -> None:
			if not quiet:
				log.critical(msg)

		filenameOrig = filename
		_, filename, ext, compression = splitFilenameExt(filename)

		plugin = None
		if format:
			plugin = cls.plugins.get(format)
			if plugin is None:
				error(f"Invalid format {format!r}")
				return None
		else:
			plugin = cls.pluginByExt.get(ext)
			if not plugin:
				plugin = cls._findPlugin(filename)
				if not plugin:
					error("Unable to detect input format!")
					return None

		if not plugin.canRead:
			error(f"plugin {plugin.name} does not support reading")
			return None

		if compression in plugin.readCompressions:
			compression = ""
			filename = filenameOrig

		return DetectedFormat(filename, plugin.name, compression)

	@classmethod
	def _outputPluginByFormat(
		cls: "type[PluginManager]",
		format: str,
	) -> "tuple[PluginProp | None, str]":
		if not format:
			return None, ""
		plugin = cls.plugins.get(format, None)
		if not plugin:
			return None, f"Invalid format {format}"
		if not plugin.canWrite:
			return None, f"plugin {plugin.name} does not support writing"
		return plugin, ""

	# TODO: breaking change:
	# return "tuple[DetectedFormat | None, str]"
	# where the str is error
	# and remove `quiet` argument, and local `error` function
	@classmethod
	def detectOutputFormat(
		cls: "type[PluginManager]",
		filename: str = "",
		format: str = "",
		inputFilename: str = "",
		quiet: bool = False,  # TODO: remove
		addExt: bool = False,
	) -> "DetectedFormat | None":
		from os.path import splitext

		# Ugh, mymy
		# https://github.com/python/mypy/issues/6549
		# > Mypy assumes that the return value of methods that return None should not
		# > be used. This helps guard against mistakes where you accidentally use the
		# > return value of such a method (e.g., saying new_list = old_list.sort()).
		# > I don't think there's a bug here.
		# Sorry, but that's not the job of a type checker at all!

		def error(msg: str) -> None:
			if not quiet:
				log.critical(msg)

		plugin, err = cls._outputPluginByFormat(format)
		if err:
			return error(err)  # type: ignore

		if not filename:
			# FIXME: not covered in tests
			if not inputFilename:
				return error(f"Invalid filename {filename!r}")  # type: ignore
			if not plugin:
				return error(
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
			return error("Unable to detect output format!")  # type: ignore

		if not plugin.canWrite:
			return error(
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
		cls: "type[PluginManager]",
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
