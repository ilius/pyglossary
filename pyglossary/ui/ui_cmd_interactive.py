#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ui_cmd_interactive.py
#
# Copyright © 2008-2020 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
sudo pip3 install prompt_toolkit
"""

import sys
import os
from os.path import dirname, join, abspath, isdir, isfile
import logging
from collections import OrderedDict

import json

# the code for cmd.Cmd is very ugly and hard to understan

# readline's complete func silently (and stupidly) hides any exception
# and only shows the print if it's in the first line of function. very awkward!

#import atexit

from prompt_toolkit import prompt as promptLow
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion.word_completer import WordCompleter

from pyglossary.core import confDir
from pyglossary.glossary import Glossary
from pyglossary.ui import ui_cmd

log = logging.getLogger("pyglossary")

indent = "\t"

cmdiConfDir = join(confDir, "cmdi")
histDir = join(cmdiConfDir, "history")

for direc in (cmdiConfDir, histDir):
	os.makedirs(direc, mode=0o700, exist_ok=True)

if __name__ == "__main__":
	Glossary.init()

pluginByDesc = {
	plugin.description: plugin
	for plugin in Glossary.plugins.values()
}
readFormatDescList = [
	Glossary.plugins[_format].description
	for _format in Glossary.readFormats
]
writeFormatDescList = [
	Glossary.plugins[_format].description
	for _format in Glossary.writeFormats
]


def dataToPrettyJson(data, ensure_ascii=False, sort_keys=False):
	return json.dumps(
		data,
		sort_keys=sort_keys,
		indent=2,
		ensure_ascii=ensure_ascii,
	)

def prompt(
	message: str,
	multiline: bool = False,
	**kwargs,
):
	text = promptLow(message=message, **kwargs)
	if multiline and text == "!m":
		print("Entering Multi-line mode, press Alt+Enter to end")
		text = promptLow(
			message="",
			multiline=True,
			**kwargs
		)
	return text


class UI(ui_cmd.UI):
	def __init__(self):
		self._inputFilename = ""
		self._outputFilename = ""
		self._inputFormat = ""
		self._outputFormat = ""
		self._prefOptions = None
		self._readOptions = None
		self._writeOptions = None
		self._convertOptions = None
		ui_cmd.UI.__init__(self)

	def paramHistoryPath(self, name: str) -> str:
		return join(histDir, f"param-{name}")

	def askFile(self, kind: str, histName: str, reading: bool):
		while True:
			filename = prompt(
				f"> {kind}: ",
				history=FileHistory(join(histDir, histName)),
				auto_suggest=AutoSuggestFromHistory(),
			)
			if filename:
				return filename
		raise ValueError(f"{kind} is not given")

	def askInputFile(self):
		return self.askFile("Input file", "filename-input", True)

	def askOutputFile(self):
		return self.askFile("Output file", "filename-output", False)

	def pluginByNameOrDesc(self, value: str) -> "Optional[PluginProp]":
		prop = pluginByDesc.get(value)
		if prop:
			return prop
		prop = Glossary.plugins.get(value)
		if prop:
			return prop
		log.error(f"internal error: invalid format name/desc {value!r}")
		return None

	def askInputFormat(self) -> str:
		history = FileHistory(join(histDir, "format-input"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			readFormatDescList + Glossary.readFormats,
			ignore_case=True,
			match_middle=True,
		)
		while True:
			value = prompt(
				"> Input format: ",
				history=history,
				auto_suggest=auto_suggest,
				completer=completer,
			)
			if not value:
				continue
			plugin = self.pluginByNameOrDesc(value)
			if plugin:
				return plugin.name
		raise ValueError("input format is not given")

	def askOutputFormat(self) -> str:
		history = FileHistory(join(histDir, "format-output"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			writeFormatDescList + Glossary.writeFormats,
			ignore_case=True,
			match_middle=True,
		)
		while True:
			value = prompt(
				"> Output format: ",
				history=history,
				auto_suggest=auto_suggest,
				completer=completer,
			)
			if not value:
				continue
			plugin = self.pluginByNameOrDesc(value)
			if plugin:
				return plugin.name
		raise ValueError("output format is not given")

	def finish(self):
		pass

	def askReadOptions(self):
		optionNames = Glossary.formatsReadOptions.get(self._inputFormat)
		if optionNames is None:
			log.error(f"internal error: invalid format {self._inputFormat!r}")
			return
		optionsProp = Glossary.plugins[self._inputFormat].optionsProp
		history = FileHistory(join(histDir, f"read-options-{self._inputFormat}"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			optionNames,
			ignore_case=True,
			match_middle=True,
		)
		while True:
			try:
				optName = prompt(
					">> ReadOption: Name [ENTER if done]: ",
					history=history,
					auto_suggest=auto_suggest,
					completer=completer,
				)
			except (KeyboardInterrupt, EOFError):
				return
			if not optName:
				return
			while True:
				try:
					optValue = prompt(
						f">>> ReadOption: {optName} = ",
						history=FileHistory(join(histDir, f"option-value-{optName}")),
						auto_suggest=AutoSuggestFromHistory(),
						default=str(self._readOptions.get(optName, "")),
					)
				except (KeyboardInterrupt, EOFError):
					break
				if optValue == "":
					if optName in self._readOptions:
						print(f"Unset read-option {optName!r}")
						del self._readOptions[optName]
					# FIXME: set empty value?
					break
				prop = optionsProp[optName]
				optValueNew, ok = prop.evaluate(optValue)
				if not ok or not prop.validate(optValueNew):
					log.error(
						f"Invalid read option value {optName}={optValue!r}"
						f" for format {self._inputFormat}"
					)
					continue
				print(f"Set read-option: {optName} = {optValueNew!r}")
				self._readOptions[optName] = optValueNew
				break

	def askWriteOptions(self):
		optionNames = Glossary.formatsWriteOptions.get(self._outputFormat)
		if optionNames is None:
			log.error(f"internal error: invalid format {self._outputFormat!r}")
			return
		optionsProp = Glossary.plugins[self._outputFormat].optionsProp
		history = FileHistory(join(histDir, f"write-options-{self._outputFormat}"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			optionNames,
			ignore_case=True,
			match_middle=True,
		)
		while True:
			try:
				optName = prompt(
					">> WriteOption: Name [ENTER if done]: ",
					history=history,
					auto_suggest=auto_suggest,
					completer=completer,
				)
			except (KeyboardInterrupt, EOFError):
				return
			if not optName:
				return
			while True:
				try:
					optValue = prompt(
						f">>> WriteOption: {optName} = ",
						history=FileHistory(join(histDir, f"option-value-{optName}")),
						auto_suggest=AutoSuggestFromHistory(),
						default=str(self._writeOptions.get(optName, "")),
					)
				except (KeyboardInterrupt, EOFError):
					break
				if optValue == "":
					if optName in self._writeOptions:
						print(f"Unset write-option {optName!r}")
						del self._writeOptions[optName]
					# FIXME: set empty value?
					break
				prop = optionsProp[optName]
				optValueNew, ok = prop.evaluate(optValue)
				if not ok or not prop.validate(optValueNew):
					log.error(
						f"Invalid write option value {optName}={optValue!r}"
						f" for format {self._outputFormat}"
					)
					continue
				print(f"Set write-option: {optName} = {optValueNew!r}")
				self._writeOptions[optName] = optValueNew
				break

	def resetReadOptions(self):
		self._readOptions = {}

	def resetWriteOptions(self):
		self._writeOptions = {}

	def showOptions(self):
		print(f"readOptions = {self._readOptions}")
		print(f"writeOptions = {self._writeOptions}")
		print(f"convertOptions = {self._convertOptions}")
		print(f"prefOptions = {self._prefOptions}")
		print()

	def setIndirect(self):
		self._convertOptions["direct"] = False
		print(f"Switched to indirect mode")

	def askFinalAction(self) -> "Optional[Callable]":
		history = FileHistory(join(histDir, "action"))
		auto_suggest = AutoSuggestFromHistory()
		actions = OrderedDict([
			("read-options", self.askReadOptions),
			("write-options", self.askWriteOptions),
			("reset-read-options", self.resetReadOptions),
			("reset-write-options", self.resetWriteOptions),
			("indirect", self.setIndirect),
			("show-options", self.showOptions),
		])
		completer = WordCompleter(
			list(actions.keys()),
			ignore_case=False,
			match_middle=True,
		)
		while True:
			action = prompt(
				"> Select action (ENTER to convert): ",
				history=history,
				auto_suggest=auto_suggest,
				completer=completer,
			)
			if not action:
				return None
			if action not in actions:
				log.error(f"invalid action: {action}")
				continue
			return actions[action]

	def askFinalOptions(self) -> bool:
		while True:
			try:
				actionFunc = self.askFinalAction()
			except (KeyboardInterrupt, EOFError):
				return False
			if actionFunc is None:
				return True  # convert
			actionFunc()

		return True  # convert

	def run(
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		prefOptions: "Optional[Dict]" = None,
		readOptions: "Optional[Dict]" = None,
		writeOptions: "Optional[Dict]" = None,
		convertOptions: "Optional[Dict]" = None,
	):
		if prefOptions is None:
			prefOptions = {}
		if readOptions is None:
			readOptions = {}
		if writeOptions is None:
			writeOptions = {}
		if convertOptions is None:
			convertOptions = {}
		if not inputFilename:
			try:
				inputFilename = self.askInputFile()
			except (KeyboardInterrupt, EOFError):
				return
		if not inputFormat:
			inputFormat = Glossary.detectInputFormat(inputFilename, quiet=True)
			if not inputFormat:
				try:
					inputFormat = self.askInputFormat()
				except (KeyboardInterrupt, EOFError):
					return
		if not outputFilename:
			try:
				outputFilename = self.askOutputFile()
			except (KeyboardInterrupt, EOFError):
				return
		if not outputFormat:
			outputArgs = Glossary.detectOutputFormat(
				filename=outputFilename,
				inputFilename=inputFilename,
				quiet=True,
			)
			if outputArgs:
				outputFormat = outputArgs[1]
			else:
				try:
					outputFormat = self.askOutputFormat()
				except (KeyboardInterrupt, EOFError):
					return

		self._inputFilename = inputFilename
		self._outputFilename = outputFilename
		self._inputFormat = inputFormat
		self._outputFormat = outputFormat
		self._prefOptions = prefOptions
		self._readOptions = readOptions
		self._writeOptions = writeOptions
		self._convertOptions = convertOptions

		if not self.askFinalOptions():
			return

		return ui_cmd.UI.run(
			self,
			self._inputFilename,
			outputFilename=self._outputFilename,
			inputFormat=self._inputFormat,
			outputFormat=self._outputFormat,
			prefOptions=self._prefOptions,
			readOptions=self._readOptions,
			writeOptions=self._writeOptions,
			convertOptions=self._convertOptions,
		)
