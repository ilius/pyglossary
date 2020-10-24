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
from os.path import dirname, join, abspath, isdir, isfile, isabs, islink
import stat
import time
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
	if kwargs.get("default", "") is None:
		kwargs["default"] = ""
	text = promptLow(message=message, **kwargs)
	if multiline and text == "!m":
		print("Entering Multi-line mode, press Alt+Enter to end")
		text = promptLow(
			message="",
			multiline=True,
			**kwargs
		)
	return text


back = "back"


class UI(ui_cmd.UI):
	def __init__(self):
		self._inputFilename = ""
		self._outputFilename = ""
		self._inputFormat = ""
		self._outputFormat = ""
		self._configOptions = None
		self._readOptions = None
		self._writeOptions = None
		self._convertOptions = None
		ui_cmd.UI.__init__(self)

		self._fsActions = OrderedDict([
			("!pwd", self.fs_pwd),
			("!ls", self.fs_ls),
			("!..", self.fs_cd_parent),
			("!cd", self.fs_cd),
		])
		self._finalActions = OrderedDict([
			("read-options", self.askReadOptions),
			("write-options", self.askWriteOptions),
			("reset-read-options", self.resetReadOptions),
			("reset-write-options", self.resetWriteOptions),
			("config", self.askConfig),
			("indirect", self.setIndirect),
			("show-options", self.showOptions),
			("back", None),
		])

	def fs_pwd(self, args: "List[str]"):
		print(os.getcwd())

	def get_ls_l(self, arg: str) -> str:
		import pwd
		import grp
		st = os.lstat(arg)
		# os.lstat does not follow sym links, like "ls" command
		details = [
			stat.filemode(st.st_mode),
			pwd.getpwuid(st.st_uid).pw_name,
			grp.getgrgid(st.st_gid).gr_name,
			str(st.st_size),
			time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
			arg,
		]
		if islink(arg):
			details.append(f"-> {os.readlink(arg)}")
		return "  ".join(details)

	def fs_ls(self, args: "List[str]"):
		if not args:
			args = [os.getcwd()]
		showTitle = len(args) > 1
		# Note: isdir and isfile funcs follow sym links, so no worry about links
		for i, arg in enumerate(args):
			if i > 0:
				print()
			if not isdir(arg):
				print(self.get_ls_l(arg))
				continue
			if showTitle:
				print(f"> List of directory {arg}:")
			for _path in os.listdir(arg):
				if isdir(_path):
					_path += "/"
				print(f"{_path}")

	def fs_cd_parent(self, args: "List[str]"):
		if args:
			log.error("This command does not take arguments")
			return
		newDir = dirname(os.getcwd())
		os.chdir(newDir)
		print(f"Changed current directory to: {newDir}")

	def fs_cd(self, args: "List[str]"):
		if len(args) != 1:
			log.error("This command takes exactly one argument")
			return
		newDir = args[0]
		if not isabs(newDir):
			newDir = abspath(newDir)
		os.chdir(newDir)
		print(f"Changed current directory to: {newDir}")

	def paramHistoryPath(self, name: str) -> str:
		return join(histDir, f"param-{name}")

	def askFile(self, kind: str, histName: str, varName: str, reading: bool):
		from shlex import split as shlex_split
		history = FileHistory(join(histDir, histName))
		auto_suggest = AutoSuggestFromHistory()
		completer_keys = list(self._fsActions.keys())
		# Note: isdir and isfile funcs follow sym links, so no worry about links
		for _path in os.listdir(os.getcwd()):
			if isdir(_path):
				continue
			completer_keys.append(_path)
		completer = WordCompleter(
			completer_keys,
			ignore_case=False,
			match_middle=False,
			sentence=True,
		)
		default = getattr(self, varName)
		while True:
			filename = prompt(
				f"> {kind}: ",
				history=history,
				auto_suggest=auto_suggest,
				completer=completer,
				default=default,
			)
			if not filename:
				continue
			parts = shlex_split(filename)
			if parts[0] in self._fsActions:
				actionFunc = self._fsActions[parts[0]]
				try:
					actionFunc(parts[1:])
				except Exception as e:
					log.exception("")
				continue
			setattr(self, varName, filename)
			return filename
		raise ValueError(f"{kind} is not given")

	def askInputFile(self):
		return self.askFile(
			"Input file",
			"filename-input",
			"_inputFilename",
			True,
		)

	def askOutputFile(self):
		return self.askFile(
			"Output file",
			"filename-output",
			"_outputFilename",
			False,
		)

	def pluginByNameOrDesc(self, value: str) -> "Optional[PluginProp]":
		plugin = pluginByDesc.get(value)
		if plugin:
			return plugin
		plugin = Glossary.plugins.get(value)
		if plugin:
			return plugin
		log.error(f"internal error: invalid format name/desc {value!r}")
		return None

	def askInputFormat(self) -> str:
		history = FileHistory(join(histDir, "format-input"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			readFormatDescList + Glossary.readFormats,
			ignore_case=True,
			match_middle=True,
			sentence=True,
		)
		while True:
			value = prompt(
				"> Input format: ",
				history=history,
				auto_suggest=auto_suggest,
				completer=completer,
				default=self._inputFormat,
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
			sentence=True,
		)
		while True:
			value = prompt(
				"> Output format: ",
				history=history,
				auto_suggest=auto_suggest,
				completer=completer,
				default=self._outputFormat,
			)
			if not value:
				continue
			plugin = self.pluginByNameOrDesc(value)
			if plugin:
				return plugin.name
		raise ValueError("output format is not given")

	def finish(self):
		pass

	# TODO: how to handle \r and \n in NewlineOption.values?

	def getOptionValueSuggestValues(self, option: "option.Option"):
		if option.values:
			return [str(x) for x in option.values]
		if option.typ == "bool":
			return ["True", "False"]
		return None

	def getOptionValueCompleter(self, option: "option.Option"):
		values = self.getOptionValueSuggestValues(option)
		if values:
			return WordCompleter(
				values,
				ignore_case=True,
				match_middle=True,
				sentence=True,
			)
		return None

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
			sentence=True,
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
			option = optionsProp[optName]
			valueCompleter = self.getOptionValueCompleter(option)
			while True:
				try:
					value = prompt(
						f">>> ReadOption: {optName} = ",
						history=FileHistory(join(histDir, f"option-value-{optName}")),
						auto_suggest=AutoSuggestFromHistory(),
						default=str(self._readOptions.get(optName, "")),
						completer=valueCompleter,
					)
				except (KeyboardInterrupt, EOFError):
					break
				if value == "":
					if optName in self._readOptions:
						print(f"Unset read-option {optName!r}")
						del self._readOptions[optName]
					# FIXME: set empty value?
					break
				valueNew, ok = option.evaluate(value)
				if not ok or not option.validate(valueNew):
					log.error(
						f"Invalid read option value {optName}={value!r}"
						f" for format {self._inputFormat}"
					)
					continue
				print(f"Set read-option: {optName} = {valueNew!r}")
				self._readOptions[optName] = valueNew
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
			sentence=True,
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
			option = optionsProp[optName]
			valueCompleter = self.getOptionValueCompleter(option)
			while True:
				try:
					value = prompt(
						f">>> WriteOption: {optName} = ",
						history=FileHistory(join(histDir, f"option-value-{optName}")),
						auto_suggest=AutoSuggestFromHistory(),
						default=str(self._writeOptions.get(optName, "")),
						completer=valueCompleter,
					)
				except (KeyboardInterrupt, EOFError):
					break
				if value == "":
					if optName in self._writeOptions:
						print(f"Unset write-option {optName!r}")
						del self._writeOptions[optName]
					# FIXME: set empty value?
					break
				valueNew, ok = option.evaluate(value)
				if not ok or not option.validate(valueNew):
					log.error(
						f"Invalid write option value {optName}={value!r}"
						f" for format {self._outputFormat}"
					)
					continue
				print(f"Set write-option: {optName} = {valueNew!r}")
				self._writeOptions[optName] = valueNew
				break

	def resetReadOptions(self):
		self._readOptions = {}

	def resetWriteOptions(self):
		self._writeOptions = {}

	def askConfig(self):
		configKeys = list(sorted(self.configDefDict.keys()))
		history = FileHistory(join(histDir, f"config-key"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			configKeys,
			ignore_case=True,
			match_middle=True,
			sentence=True,
		)
		while True:
			try:
				configKey = prompt(
					">> Config: Key [ENTER if done]: ",
					history=history,
					auto_suggest=auto_suggest,
					completer=completer,
				)
			except (KeyboardInterrupt, EOFError):
				return
			if not configKey:
				return
			option = self.configDefDict[configKey]
			valueCompleter = self.getOptionValueCompleter(option)
			while True:
				try:
					value = prompt(
						f">>> Config: {configKey} = ",
						history=FileHistory(join(histDir, f"config-value-{configKey}")),
						auto_suggest=AutoSuggestFromHistory(),
						default=str(self._configOptions.get(configKey, "")),
						completer=valueCompleter,
					)
				except (KeyboardInterrupt, EOFError):
					break
				if value == "":
					if configKey in self._configOptions:
						print(f"Unset config {configKey!r}")
						del self._configOptions[configKey]
					# FIXME: set empty value?
					break
				valueNew, ok = option.evaluate(value)
				if not ok or not option.validate(valueNew):
					log.error(
						f"Invalid config value {configKey}={value!r}"
					)
					continue
				print(f"Set config: {configKey} = {valueNew!r}")
				self._configOptions[configKey] = valueNew
				break

	def showOptions(self):
		print(f"readOptions = {self._readOptions}")
		print(f"writeOptions = {self._writeOptions}")
		print(f"convertOptions = {self._convertOptions}")
		print(f"configOptions = {self._configOptions}")
		print()

	def setIndirect(self):
		self._convertOptions["direct"] = False
		print(f"Switched to indirect mode")

	def askFinalAction(self) -> "Optional[str]":
		history = FileHistory(join(histDir, "action"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			list(self._finalActions.keys()),
			ignore_case=False,
			match_middle=True,
			sentence=True,
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
			if action not in self._finalActions:
				log.error(f"invalid action: {action}")
				continue
			return action

	def askFinalOptions(self) -> "Union[bool, Literal[back]]":
		while True:
			try:
				action = self.askFinalAction()
			except (KeyboardInterrupt, EOFError):
				return False
			except Exception as e:
				log.exception("")
				return False
			if action == back:
				return back
			if action is None:
				return True  # convert
			actionFunc = self._finalActions[action]
			if actionFunc is None:
				return True  # convert
			actionFunc()

		return True  # convert

	def getRunKeywordArgs(self) -> "Dict":
		return dict(
			inputFilename=self._inputFilename,
			outputFilename=self._outputFilename,
			inputFormat=self._inputFormat,
			outputFormat=self._outputFormat,
			configOptions=self._configOptions,
			readOptions=self._readOptions,
			writeOptions=self._writeOptions,
			convertOptions=self._convertOptions,
		)

	def checkInputFormat(self, forceAsk: bool = False):
		if not forceAsk:
			inputFormat = Glossary.detectInputFormat(self._inputFilename, quiet=True)
			if inputFormat:
				self._inputFormat = inputFormat
				return
		self._inputFormat = self.askInputFormat()

	def checkOutputFormat(self, forceAsk: bool = False):
		if not forceAsk:
			outputArgs = Glossary.detectOutputFormat(
				filename=self._outputFilename,
				inputFilename=self._inputFilename,
				quiet=True,
			)
			if outputArgs:
				self._outputFormat = outputArgs[1]
				return
		self._outputFormat = self.askOutputFormat()

	def askInputOutputAgain(self):
		self.askInputFile()
		self.checkInputFormat(forceAsk=True)
		self.askOutputFile()
		self.checkOutputFormat(forceAsk=True)

	def run(
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		configOptions: "Optional[Dict]" = None,
		readOptions: "Optional[Dict]" = None,
		writeOptions: "Optional[Dict]" = None,
		convertOptions: "Optional[Dict]" = None,
	):
		if configOptions is None:
			configOptions = {}
		if readOptions is None:
			readOptions = {}
		if writeOptions is None:
			writeOptions = {}
		if convertOptions is None:
			convertOptions = {}

		self._inputFilename = inputFilename
		self._outputFilename = outputFilename
		self._inputFormat = inputFormat
		self._outputFormat = outputFormat
		self._configOptions = configOptions
		self._readOptions = readOptions
		self._writeOptions = writeOptions
		self._convertOptions = convertOptions

		del inputFilename, outputFilename, inputFormat, outputFormat
		del configOptions, readOptions, writeOptions, convertOptions

		if not self._inputFilename:
			try:
				self.askInputFile()
			except (KeyboardInterrupt, EOFError):
				return
		if not self._inputFormat:
			try:
				self.checkInputFormat()
			except (KeyboardInterrupt, EOFError):
				return
		if not self._outputFilename:
			try:
				self.askOutputFile()
			except (KeyboardInterrupt, EOFError):
				return
		if not self._outputFormat:
			try:
				self.checkOutputFormat()
			except (KeyboardInterrupt, EOFError):
				return

		while True:
			status = self.askFinalOptions()
			if status == back:
				self.askInputOutputAgain()
				continue
			if not status:
				return
			try:
				succeed = ui_cmd.UI.run(self, **self.getRunKeywordArgs())
			except Exception as e:
				log.exception("")
			else:
				if succeed:
					return succeed
			print("Press Control + C to exit")
