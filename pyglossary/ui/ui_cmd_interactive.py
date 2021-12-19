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
To use this user interface:
	sudo pip3 install prompt_toolkit
"""

# GitHub repo for prompt_toolkit
# https://github.com/prompt-toolkit/python-prompt-toolkit

# The code for Python's cmd.Cmd was very ugly and hard to understand last I
# cheched. But we don't use cmd module here, and nor does prompt_toolkit.

# Completion func for Python's readline, silently (and stupidly) hides any
# exception, and only shows the print if it's in the first line of function.
# very awkward!
# We also don't use readline module, and nor does prompt_toolkit.
# Looks like prompt_toolkit works directly with sys.stdin, sys.stdout
# and sys.stderr.

# prompt_toolkit also supports ncurses-like dialogs with buttons and widgets,
# but I prefer this kind of UI with auto-completion and history

import sys
import os
from os.path import (
	dirname,
	join,
	abspath,
	relpath,
	isdir,
	isabs,
)
import logging
from collections import OrderedDict
import argparse

import json

from pyglossary.core import confDir
from pyglossary.glossary import Glossary
from pyglossary.ui import ui_cmd


from prompt_toolkit import prompt as promptLow
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import (
	WordCompleter,
	PathCompleter,
	Completion,
)
from prompt_toolkit.shortcuts import confirm, PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys


class MiniCheckBoxPrompt(object):
	def __init__(
		self,
		message: str = "",
		fmt: str = "{message}: {check}",
		value: bool = False,
	):
		self.message = message
		self.fmt = fmt
		self.value = value

	def formatMessage(self):
		return self.fmt.format(
			check="[x]" if self.value else "[ ]",
			message=self.message,
		)

	def __pt_formatted_text__(self):
		return [("", self.formatMessage())]


def checkbox_prompt(
	message: str,
	default: bool,
) -> PromptSession[bool]:
	"""
	Create a `PromptSession` object for the 'confirm' function.
	"""
	bindings = KeyBindings()

	check = MiniCheckBoxPrompt(message=message, value=default)

	@bindings.add(" ")
	def space(event: "E") -> None:
		check.value = not check.value
		# cursor_pos = check.formatMessage().find("[") + 1
		# cur_cursor_pos = session.default_buffer.cursor_position
		# print(f"cur_cursor_pos={cur_cursor_pos}, cursor_pos={cursor_pos}")
		# session.default_buffer.cursor_position = cursor_pos

	@bindings.add(Keys.Any)
	def _(event: "E") -> None:
		" Disallow inserting other text. "
		pass

	complete_message = check
	session: PromptSession[bool] = PromptSession(
		complete_message,
		key_bindings=bindings
	)
	session.prompt()
	return check.value


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
		print("Entering Multi-line mode, press Alt+ENTER to end")
		text = promptLow(
			message="",
			multiline=True,
			**kwargs
		)
	return text


back = "back"


class MyPathCompleter(PathCompleter):
	def __init__(
		self,
		reading: bool,
		fs_action_names=None,
		**kwargs
	):
		PathCompleter.__init__(
			self,
			file_filter=self.file_filter,
			**kwargs
		)
		if fs_action_names is None:
			fs_action_names = []
		self.fs_action_names = fs_action_names

	def file_filter(self, filename: str) -> bool:
		# filename is full/absoule file path
		return True

	# def get_completions_exception(document, complete_event, e):
	# 	log.error(f"Execption in get_completions: {e}")

	def get_completions(
		self,
		document: "Document",
		complete_event: "CompleteEvent",
	) -> "Iterable[Completion]":
		text = document.text_before_cursor

		for action in self.fs_action_names:
			if action.startswith(text):
				yield Completion(
					text=action,
					start_position=-len(text),
					display=action,
				)

		yield from PathCompleter.get_completions(
			self,
			document=document,
			complete_event=complete_event,
		)


class AbsolutePathHistory(FileHistory):
	def load_history_strings(self) -> "Iterable[str]":
		# pwd = os.getcwd()
		pathList = FileHistory.load_history_strings(self)
		return [
			relpath(p)
			for p in pathList
		]

	def store_string(self, string: str) -> None:
		FileHistory.store_string(self, abspath(string))


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

		self.ls_parser = argparse.ArgumentParser(add_help=False)
		self.ls_parser.add_argument(
			"-l",
			"--long",
			action="store_true",
			dest="long",
			help="use a long listing format",
		)
		self.ls_parser.add_argument(
			"--help",
			action="store_true",
			dest="help",
			help="display help",
		)
		self.ls_usage = (
			'Usage: !ls [--help] [-l] [FILE/DIRECTORY]...\n\n'
			'optional arguments:\n'
			'    --help      show this help message and exit\n'
			'    -l, --long  use a long listing format\n'
		)

		self._fsActions = OrderedDict([
			("!pwd", (self.fs_pwd, "")),
			("!ls", (self.fs_ls, self.ls_usage)),
			("!..", (self.fs_cd_parent, "")),
			("!cd", (self.fs_cd, "")),
		])
		self._finalActions = OrderedDict([
			("formats", self.askFormats),
			("read-options", self.askReadOptions),
			("write-options", self.askWriteOptions),
			("reset-read-options", self.resetReadOptions),
			("reset-write-options", self.resetWriteOptions),
			("config", self.askConfig),
			("indirect", self.setIndirect),
			("sqlite", self.setSQLite),
			("no-progressbar", self.setNoProgressbar),
			("sort", self.setSort),
			("show-options", self.showOptions),
			("back", None),
		])

	def fs_pwd(self, args: "List[str]"):
		print(os.getcwd())

	def get_ls_l(
		self,
		arg: str,
		st: "Optional[os.stat_result]" = None,
		parentDir: str = "",
		sizeWidth: int = 0,
	) -> str:
		import stat
		import pwd
		import grp
		import time
		argPath = arg
		if parentDir:
			argPath = join(parentDir, arg)
		if st is None:
			st = os.lstat(argPath)
		# os.lstat does not follow sym links, like "ls" command
		details = [
			stat.filemode(st.st_mode),
			pwd.getpwuid(st.st_uid).pw_name,
			grp.getgrgid(st.st_gid).gr_name,
			str(st.st_size).rjust(sizeWidth),
			time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
			arg,
		]
		if stat.S_ISLNK(st.st_mode):
			details.append(f"-> {os.readlink(argPath)}")
		return "  ".join(details)

	def fs_ls(self, args: "List[str]"):
		opts, args = self.ls_parser.parse_known_args(args=args)

		if opts.help:
			print(self.ls_usage)
			return

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
				print(f"> List of directory {arg!r}:")

			if not opts.long:
				for _path in os.listdir(arg):
					if isdir(_path):
						_path += "/"
					print(f"{_path}")
				continue

			contents = os.listdir(arg)
			statList = [
				os.lstat(join(arg, _path))
				for _path in contents
			]
			maxFileSize = max([
				st.st_size
				for st in statList
			])
			sizeWidth = len(str(maxFileSize))
			for i, _path in enumerate(contents):
				print(self.get_ls_l(
					_path,
					parentDir=arg,
					st=statList[i],
					sizeWidth=sizeWidth,
				))

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

	def askFile(self, kind: str, histName: str, varName: str, reading: bool):
		from shlex import split as shlex_split
		history = AbsolutePathHistory(join(histDir, histName))
		auto_suggest = AutoSuggestFromHistory()
		# Note: isdir and isfile funcs follow sym links, so no worry about links
		completer = MyPathCompleter(
			reading=reading,
			fs_action_names=list(self._fsActions.keys()),
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
				actionFunc, usage = self._fsActions[parts[0]]
				try:
					actionFunc(parts[1:])
				except Exception as e:
					log.exception("")
					if usage:
						print("\n" + usage)
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
		plugin = Glossary.plugins[self._inputFormat]
		options = Glossary.formatsReadOptions.get(self._inputFormat)
		if options is None:
			log.error(f"internal error: invalid format {self._inputFormat!r}")
			return
		optionsProp = Glossary.plugins[self._inputFormat].optionsProp
		history = FileHistory(join(histDir, f"read-options-{self._inputFormat}"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			options.keys(),
			ignore_case=True,
			match_middle=True,
			sentence=True,
		)
		while True:
			try:
				optName = prompt(
					">> ReadOption: Name (ENTER if done): ",
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
			default = self._readOptions.get(optName)
			if default is None:
				default = options[optName]
			print(f"Comment: {option.longComment}")
			while True:
				if option.typ == "bool":
					try:
						valueNew = checkbox_prompt(
							f">>> ReadOption: {optName}",
							default=default,
						)
					except (KeyboardInterrupt, EOFError):
						break
					print(f"Set read-option: {optName} = {valueNew!r}")
					self._readOptions[optName] = valueNew
					break
				try:
					value = prompt(
						f">>> ReadOption: {optName} = ",
						history=FileHistory(join(histDir, f"option-value-{optName}")),
						auto_suggest=AutoSuggestFromHistory(),
						default=str(default),
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
		plugin = Glossary.plugins[self._inputFormat]
		options = Glossary.formatsWriteOptions.get(self._outputFormat)
		if options is None:
			log.error(f"internal error: invalid format {self._outputFormat!r}")
			return
		optionsProp = Glossary.plugins[self._outputFormat].optionsProp
		history = FileHistory(join(histDir, f"write-options-{self._outputFormat}"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			options.keys(),
			ignore_case=True,
			match_middle=True,
			sentence=True,
		)
		while True:
			try:
				optName = prompt(
					">> WriteOption: Name (ENTER if done): ",
					history=history,
					auto_suggest=auto_suggest,
					completer=completer,
				)
			except (KeyboardInterrupt, EOFError):
				return
			if not optName:
				return
			option = optionsProp[optName]
			print(f"Comment: {option.longComment}")
			valueCompleter = self.getOptionValueCompleter(option)
			default = self._writeOptions.get(optName)
			if default is None:
				default = options[optName]
			while True:
				if option.typ == "bool":
					try:
						valueNew = checkbox_prompt(
							f">>> WriteOption: {optName}",
							default=default,
						)
					except (KeyboardInterrupt, EOFError):
						break
					print(f"Set write-option: {optName} = {valueNew!r}")
					self._writeOptions[optName] = valueNew
					break
				try:
					value = prompt(
						f">>> WriteOption: {optName} = ",
						history=FileHistory(join(histDir, f"option-value-{optName}")),
						auto_suggest=AutoSuggestFromHistory(),
						default=str(default),
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

	def askConfigValue(self, configKey, option):
		default = self.config.get(configKey, "")
		if option.typ == "bool":
			return str(checkbox_prompt(
				message=f">>> Config: {configKey}",
				default=bool(default),
			))
		return prompt(
			f">>> Config: {configKey} = ",
			history=FileHistory(join(histDir, f"config-value-{configKey}")),
			auto_suggest=AutoSuggestFromHistory(),
			default=str(default),
			completer=self.getOptionValueCompleter(option),
		)

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
					">> Config: Key (ENTER if done): ",
					history=history,
					auto_suggest=auto_suggest,
					completer=completer,
				)
			except (KeyboardInterrupt, EOFError):
				return
			if not configKey:
				return
			option = self.configDefDict[configKey]
			while True:
				try:
					value = self.askConfigValue(configKey, option)
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
				self.config[configKey] = valueNew
				break

	def showOptions(self):
		print(f"readOptions = {self._readOptions}")
		print(f"writeOptions = {self._writeOptions}")
		print(f"convertOptions = {self._convertOptions}")
		print(f"configOptions = {self._configOptions}")
		print()

	def setIndirect(self):
		self._convertOptions["direct"] = False
		self._convertOptions["sqlite"] = None
		print("Switched to indirect mode")

	def setSQLite(self):
		self._convertOptions["direct"] = None
		self._convertOptions["sqlite"] = True
		print("Switched to SQLite mode")

	def setNoProgressbar(self):
		self._convertOptions["progressbar"] = False
		print("Disabled progress bar")

	def setSort(self):
		from pyglossary.entry import Entry
		try:
			value = checkbox_prompt(
				message=f">> Enable Sort",
				default=self._convertOptions.get("sort", False),
			)
		except (KeyboardInterrupt, EOFError):
			return
		self._convertOptions["sort"] = value
		if value:
			self._convertOptions["defaultSortKey"] = Entry.defaultSortKey

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
			glossarySetAttrs=self._glossarySetAttrs,
		)

	def checkInputFormat(self, forceAsk: bool = False):
		if not forceAsk:
			inputArgs = Glossary.detectInputFormat(self._inputFilename, quiet=True)
			if inputArgs:
				inputFormat = inputArgs[1]
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

	def askFormats(self):
		self.checkInputFormat(forceAsk=True)
		self.checkOutputFormat(forceAsk=True)

	def askInputOutputAgain(self):
		self.askInputFile()
		self.checkInputFormat(forceAsk=True)
		self.askOutputFile()
		self.checkOutputFormat(forceAsk=True)

	def printNonInteractiveCommand(self):
		from shlex import quote
		cmd = [
			ui_cmd.COMMAND,
			quote(self._inputFilename),
			quote(self._outputFilename),
			quote(f"--read-format={self._inputFormat}"),
			quote(f"--write-format={self._outputFormat}"),
		]

		if self._readOptions:
			optionsJson = json.dumps(self._readOptions, ensure_ascii=True)
			cmd.append(quote(f"--json-read-options={optionsJson}"))

		if self._writeOptions:
			optionsJson = json.dumps(self._writeOptions, ensure_ascii=True)
			cmd.append(quote(f"--json-write-options={optionsJson}"))

		if self._configOptions:
			for key, value in self._configOptions.items():
				if value is None:
					continue
				option = self.configDefDict.get(key)
				if option is None:
					log.error(f"config key {key} was not found")
				if not option.cmd:
					log.error(f"config key {key} has no command line flag")
				flag = option.cmdFlag
				if not flag:
					flag = key.replace('_', '-')
				if option.typ == "bool":
					if not value:
						flag = f"no-{flag}"
					cmd.append(f"--{flag}")
				else:
					cmd.append(quote(f"--{flag}={value}"))

		if self._convertOptions:
			convertOptionsFlags = {
				"direct": ("indirect", "direct"),
				"sqlite": ("", "sqlite"),
				"progressbar": ("no-progress-bar", ""),
				"sort": ("no-sort", "sort"),
				"sortCacheSize": ("sort-cache-size", ""),
				"defaultSortKey": None,
			}
			for key, value in self._convertOptions.items():
				if value is None:
					continue
				if key not in convertOptionsFlags:
					log.error(f"unknow key {key} in convertOptions")
					continue
				ftup = convertOptionsFlags[key]
				if ftup is None:
					continue
				if isinstance(value, bool):
					flag = ftup[int(value)]
					if flag:
						cmd.append(f"--{flag}")
				else:
					flag = ftup[0]
					cmd.append(f"--{flag}={value}")

		print()
		print(
			"If you want to repeat this conversion later, "
			"you can use this command:"
		)
		print(" ".join(cmd))

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
		glossarySetAttrs: "Optional[Dict]" = None,
	):
		if configOptions is None:
			configOptions = {}
		if readOptions is None:
			readOptions = {}
		if writeOptions is None:
			writeOptions = {}
		if convertOptions is None:
			convertOptions = {}
		if glossarySetAttrs is None:
			glossarySetAttrs = {}

		self._inputFilename = inputFilename
		self._outputFilename = outputFilename
		self._inputFormat = inputFormat
		self._outputFormat = outputFormat
		self._configOptions = configOptions
		self._readOptions = readOptions
		self._writeOptions = writeOptions
		self._convertOptions = convertOptions
		self._glossarySetAttrs = glossarySetAttrs

		del inputFilename, outputFilename, inputFormat, outputFormat
		del configOptions, readOptions, writeOptions, convertOptions

		self.loadConfig(**self._configOptions)

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
				self.printNonInteractiveCommand()
				if succeed:
					if self._configOptions and confirm("Save Config?"):
						self.saveConfig()
					return succeed
			print("Press Control + C to exit")
