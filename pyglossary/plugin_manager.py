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
import sys
import os

from .plugin_prop import PluginProp
from .glossary_utils import (
	splitFilenameExt,
)

log = logging.getLogger("pyglossary")


class PluginManager(object):
	plugins = {}  # type: Dict[str, PluginProp]
	pluginByExt = {}  # type: Dict[str, PluginProp]

	formatsReadOptions = {}  # type: Dict[str, OrderedDict[str, Any]]
	formatsWriteOptions = {}  # type: Dict[str, OrderedDict[str, Any]]
	# for example formatsReadOptions[format][optName] gives you the default value

	readFormats = []  # type: List[str]
	writeFormats = []  # type: List[str]

	@classmethod
	def loadPlugins(cls: "ClassVar", directory: str) -> None:
		"""
		executed on startup.  as name implies, loads plugins from directory
		"""
		import pkgutil
		from os.path import isdir

		# log.debug(f"Loading plugins from directory: {directory!r}")
		if not isdir(directory):
			log.critical(f"Invalid plugin directory: {directory!r}")
			return

		pluginNames = [
			pluginName
			for _, pluginName, _ in pkgutil.iter_modules([directory])
		]
		pluginNames.sort()

		sys.path.append(directory)
		for pluginName in pluginNames:
			cls.loadPlugin(pluginName)
		sys.path.pop()

	@classmethod
	def loadPlugin(cls: "ClassVar", pluginName: str) -> None:
		try:
			plugin = __import__(pluginName)
		except ModuleNotFoundError as e:
			log.warning(f"Module {e.name!r} not found, skipping plugin {pluginName!r}")
			return
		except Exception as e:
			log.exception(f"Error while importing plugin {pluginName}")
			return

		if (not hasattr(plugin, "enable")) or (not plugin.enable):
			# log.debug(f"Plugin disabled or not a plugin: {pluginName}")
			return

		format = plugin.format

		extensions = plugin.extensions
		if not isinstance(extensions, tuple):
			msg = f"{format} plugin: extensions must be tuple"
			if isinstance(extensions, list):
				extensions = tuple(extensions)
				log.error(msg)
			else:
				raise ValueError(msg)

		if hasattr(plugin, "description"):
			desc = plugin.description
		else:
			desc = f"{format} ({extensions[0]})"

		prop = PluginProp(plugin)

		cls.plugins[format] = prop

		for ext in extensions:
			if ext.lower() != ext:
				log.error(f"non-lowercase extension={ext!r} in {pluginName} plugin")
			cls.pluginByExt[ext.lstrip(".")] = prop
			cls.pluginByExt[ext] = prop

		Reader = prop.readerClass
		if Reader is not None:
			options = prop.getReadOptions()
			cls.formatsReadOptions[format] = options
			cls.readFormats.append(format)
			Reader.formatName = format

		Writer = prop.writerClass
		if Writer is not None:
			options = prop.getWriteOptions()
			cls.formatsWriteOptions[format] = options
			cls.writeFormats.append(format)

		if not (Reader or Writer):
			log.warning(f"plugin {format} has no Reader nor Writer")

		if hasattr(plugin, "write"):
			log.error(
				f"plugin {format} has write function, "
				f"must migrate to Writer class"
			)

		return plugin

	@classmethod
	def findPlugin(cls, query: str) -> "Optional[PluginProp]":
		"""
			find plugin by name or extention
		"""
		plugin = cls.plugins.get(query)
		if plugin:
			return plugin
		plugin = cls.pluginByExt.get(query)
		if plugin:
			return plugin
		return None

	@classmethod
	def detectInputFormat(
		cls,
		filename: str,
		format: str = "",
		quiet: bool = False,
	) -> "Optional[Tuple[str, str, str]]":
		"""
			returns (filename, format, compression) or None
		"""

		def error(msg: str) -> None:
			if not quiet:
				log.critical(msg)
			return None

		filenameOrig = filename
		filenameNoExt, filename, ext, compression = splitFilenameExt(filename)

		plugin = None
		if format:
			plugin = cls.plugins.get(format)
			if plugin is None:
				return error(f"Invalid format {format!r}")
		else:
			plugin = cls.pluginByExt.get(ext)
			if not plugin:
				plugin = cls.findPlugin(filename)
				if not plugin:
					return error("Unable to detect input format!")

		if not plugin.canRead:
			return error(f"plugin {plugin.name} does not support reading")

		if compression in getattr(plugin.readerClass, "compressions", []):
			compression = ""
			filename = filenameOrig

		return filename, plugin.name, compression

	@classmethod
	def detectOutputFormat(
		cls,
		filename: str = "",
		format: str = "",
		inputFilename: str = "",
		quiet: bool = False,
		addExt: bool = False,
	) -> "Optional[Tuple[str, str, str]]":
		"""
		returns (filename, format, compression) or None
		"""
		from os.path import splitext

		def error(msg: str) -> None:
			if not quiet:
				log.critical(msg)
			return None

		plugin = None
		if format:
			plugin = cls.plugins.get(format)
			if not plugin:
				return error(f"Invalid format {format}")
			if not plugin.canWrite:
				return error(f"plugin {plugin.name} does not support writing")

		if not filename:
			if not inputFilename:
				return error(f"Invalid filename {filename!r}")
			if not plugin:
				return error("No filename nor format is given for output file")
			filename = splitext(inputFilename)[0] + plugin.ext
			return filename, plugin.name, ""

		filenameOrig = filename
		filenameNoExt, filename, ext, compression = splitFilenameExt(filename)

		if not plugin:
			plugin = cls.pluginByExt.get(ext)
			if not plugin:
				plugin = cls.findPlugin(filename)

		if not plugin:
			return error("Unable to detect output format!")

		if not plugin.canWrite:
			return error(f"plugin {plugin.name} does not support writing")

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

		return filename, plugin.name, compression
