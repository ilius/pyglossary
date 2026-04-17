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

"""
Interactive terminal UI: prompts for paths, formats, plugin options, then converts.

State is split between :class:`ConversionSession` (conversion parameters) and
:class:`InteractivePrompt` (prompting and ``!`` shell helpers). Global settings
use ``self.config`` from :class:`~pyglossary.ui.base.UIBase` (load/save).
"""

from __future__ import annotations

import json
import logging
import os
import shlex
from os.path import join
from typing import TYPE_CHECKING, Any

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import confirm

from pyglossary.core import confDir
from pyglossary.glossary_v2 import Error, Glossary
from pyglossary.sort_keys import lookupSortKey, namedSortKeyList
from pyglossary.ui import ui_cmd
from pyglossary.ui.config import configDefDict

from .conversion_session import ConversionSession
from .history import AbsolutePathHistory
from .interactive_prompt import InteractivePrompt
from .path_comp import MyPathCompleter

if TYPE_CHECKING:
	from pyglossary.config_type import ConfigType
	from pyglossary.option import Option
	from pyglossary.plugin_prop import PluginProp

__all__ = ["UI"]

# GitHub repo for prompt_toolkit
# https://github.com/prompt-toolkit/python-prompt-toolkit
# The code for Python's cmd.Cmd was very ugly and hard to understand last I
# checked. But we don't use cmd module here, and nor does prompt_toolkit.
# Completion func for Python's readline, silently (and stupidly) hides any
# exception, and only shows the print if it's in the first line of function.
# very awkward!
# We also don't use readline module, and nor does prompt_toolkit.
# Looks like prompt_toolkit works directly with sys.stdin, sys.stdout
# and sys.stderr.
# prompt_toolkit also supports ncurses-like dialogs with buttons and widgets,
# but I prefer this kind of UI with auto-completion and history


log = logging.getLogger("pyglossary")

indent = "\t"

cmdiConfDir = join(confDir, "cmdi")
histDir = join(cmdiConfDir, "history")

for direc in (cmdiConfDir, histDir):
	os.makedirs(direc, mode=0o700, exist_ok=True)

if __name__ == "__main__":
	Glossary.init()

pluginByDesc = {plugin.description: plugin for plugin in Glossary.plugins.values()}
readFormatDescList = [
	Glossary.plugins[format_].description for format_ in Glossary.readFormats
]
writeFormatDescList = [
	Glossary.plugins[format_].description for format_ in Glossary.writeFormats
]

convertOptionsFlags = {
	"direct": ("indirect", "direct"),
	"sqlite": ("", "sqlite"),
	"sort": ("no-sort", "sort"),
}
infoOverrideFlags = {
	"sourceLang": "source-lang",
	"targetLang": "target-lang",
	"name": "name",
}


back = "back"


class UI(ui_cmd.UI):
	"""
	prompt_toolkit-based interactive front-end to glossary conversion.

	Extends :class:`pyglossary.ui.ui_cmd.UI` with a multi-step flow: choose input
	and output paths, detect or choose formats, optionally adjust read/write
	options and conversion flags, then run :meth:`pyglossary.ui.ui_cmd.UI.run`.
	After a successful conversion, prints an equivalent non-interactive shell
	command for replay.
	"""

	def __init__(
		self,
		progressbar: bool = True,
	) -> None:
		"""Create session and prompt helpers and register post-conversion menu actions."""
		self._session = ConversionSession()
		self._prompt = InteractivePrompt()
		self.config: ConfigType = {}
		ui_cmd.UI.__init__(
			self,
			progressbar=progressbar,
		)

		self._finalActions = {
			"formats": self.askFormats,
			"read-options": self.askReadOptions,
			"write-options": self.askWriteOptions,
			"reset-read-options": self.resetReadOptions,
			"reset-write-options": self.resetWriteOptions,
			"config": self.askConfig,
			"indirect": self.setIndirect,
			"sqlite": self.setSQLite,
			"no-progressbar": self.setNoProgressbar,
			"sort": self.setSort,
			"sort-key": self.setSortKey,
			"show-options": self.showOptions,
			"back": None,
		}

	def askFile(
		self,
		kind: str,
		histName: str,
		session_attr: str,
		reading: bool,
	) -> str:
		"""
		Prompt for a path; run ``!`` shell actions or store the path on ``_session``.

		``session_attr`` names a :class:`ConversionSession` field (e.g.
		``inputFilename``). ``histName`` selects the history file under
		``cmdi/history``. Re-prompts until a non-empty path is chosen or a shell
		command completes.
		"""
		from shlex import split as shlex_split

		history = AbsolutePathHistory(join(histDir, histName))
		auto_suggest = AutoSuggestFromHistory()
		# Note: isdir and isfile funcs follow sym links, so no worry about links
		completer = MyPathCompleter(
			reading=reading,
			fs_action_names=list(self._prompt.fs_actions),
		)
		default = getattr(self._session, session_attr)
		while True:
			filename = self._prompt.prompt(
				1,
				kind,
				history=history,
				auto_suggest=auto_suggest,
				completer=completer,
				default=default,
			)
			if not filename:
				continue
			try:
				parts = shlex_split(filename)
			except ValueError:
				# file name can have single/double quote
				setattr(self._session, session_attr, filename)
				return filename
			if parts[0] in self._prompt.fs_actions:
				actionFunc, usage = self._prompt.fs_actions[parts[0]]
				try:
					actionFunc(parts[1:])
				except Exception:
					log.exception("")
					if usage:
						print("\n" + usage)
				continue
			setattr(self._session, session_attr, filename)
			return filename
		raise ValueError(f"{kind} is not given")

	def askInputFile(self) -> str:
		"""Prompt for the glossary input path (with read-oriented completion)."""
		return self.askFile(
			"Input file",
			"filename-input",
			"inputFilename",
			True,
		)

	def askOutputFile(self) -> str:
		"""Prompt for the glossary output path."""
		return self.askFile(
			"Output file",
			"filename-output",
			"outputFilename",
			False,
		)

	@staticmethod
	def pluginByNameOrDesc(value: str) -> PluginProp | None:
		"""Resolve a plugin by user-visible description or internal format name."""
		plugin = pluginByDesc.get(value)
		if plugin:
			return plugin
		plugin = Glossary.plugins.get(value)
		if plugin:
			return plugin
		log.error(f"internal error: invalid format name/desc {value!r}")
		return None

	def askInputFormat(self) -> str:
		"""Prompt until a valid read format name or description is entered."""
		history = FileHistory(join(histDir, "format-input"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			readFormatDescList + Glossary.readFormats,
			ignore_case=True,
			match_middle=True,
			sentence=True,
		)
		while True:
			value = self._prompt.prompt(
				1,
				"Input format",
				history=history,
				auto_suggest=auto_suggest,
				completer=completer,
				default=self._session.inputFormat,
			)
			if not value:
				continue
			plugin = self.pluginByNameOrDesc(value)
			if plugin:
				return plugin.name
		raise ValueError("input format is not given")

	def askOutputFormat(self) -> str:
		"""Prompt until a valid write format name or description is entered."""
		history = FileHistory(join(histDir, "format-output"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			writeFormatDescList + Glossary.writeFormats,
			ignore_case=True,
			match_middle=True,
			sentence=True,
		)
		while True:
			value = self._prompt.prompt(
				1,
				"Output format",
				history=history,
				auto_suggest=auto_suggest,
				completer=completer,
				default=self._session.outputFormat,
			)
			if not value:
				continue
			plugin = self.pluginByNameOrDesc(value)
			if plugin:
				return plugin.name
		raise ValueError("output format is not given")

	def finish(self) -> None:
		"""Hook for end-of-flow; unused in this UI."""

	# TODO: how to handle \r and \n in NewlineOption.values?

	@staticmethod
	def getOptionValueSuggestValues(option: Option) -> list[str] | None:
		"""Return discrete choices for tab-completion, or None for free text."""
		if option.values:
			return [str(x) for x in option.values]
		if option.typ == "bool":
			return ["True", "False"]
		return None

	def getOptionValueCompleter(self, option: Option) -> WordCompleter | None:
		"""Build a ``WordCompleter`` when the option has a bounded value set."""
		values = self.getOptionValueSuggestValues(option)
		if values:
			return WordCompleter(
				values,
				ignore_case=True,
				match_middle=True,
				sentence=True,
			)
		return None

	# PLR0912 Too many branches (15 > 12)
	def askReadOptions(self) -> None:  # noqa: PLR0912
		"""
		Interactively edit read options for the current input format.

		Updates :attr:`ConversionSession.readOptions`.
		"""
		options = Glossary.formatsReadOptions.get(self._session.inputFormat)
		if options is None:
			log.error(f"internal error: invalid format {self._session.inputFormat!r}")
			return
		optionsProp = Glossary.plugins[self._session.inputFormat].optionsProp
		history = FileHistory(join(histDir, f"read-options-{self._session.inputFormat}"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			list(options),
			ignore_case=True,
			match_middle=True,
			sentence=True,
		)
		while True:
			try:
				optName = self._prompt.prompt(
					2,
					"ReadOption: Name (ENTER if done)",
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
			default = self._session.readOptions.get(optName)
			if default is None:
				default = options[optName]
			print(f"Comment: {option.longComment}")
			while True:
				if option.typ == "bool":
					try:
						valueNew = self._prompt.checkbox_prompt(
							3,
							f"ReadOption: {optName}",
							default=default,
						)
					except (KeyboardInterrupt, EOFError):
						break
					print(f"Set read-option: {optName} = {valueNew!r}")
					self._session.readOptions[optName] = valueNew
					break
				try:
					value = self._prompt.prompt(
						3,
						f"ReadOption: {optName}",
						colon=" =",
						history=FileHistory(join(histDir, f"option-value-{optName}")),
						auto_suggest=AutoSuggestFromHistory(),
						default=str(default),
						completer=valueCompleter,
					)
				except (KeyboardInterrupt, EOFError):
					break
				if value == "" and option.typ != "str":  # noqa: PLC1901
					if optName in self._session.readOptions:
						print(f"Unset read-option {optName!r}")
						del self._session.readOptions[optName]
					break
				valueNew, ok = option.evaluate(value)
				if not ok or not option.validate(valueNew):
					log.error(
						f"Invalid read option value {optName}={value!r}"
						f" for format {self._session.inputFormat}",
					)
					continue
				print(f"Set read-option: {optName} = {valueNew!r}")
				self._session.readOptions[optName] = valueNew
				break

	# PLR0912 Too many branches (15 > 12)
	def askWriteOptions(self) -> None:  # noqa: PLR0912
		"""
		Interactively edit write options for the current output format.

		Updates :attr:`ConversionSession.writeOptions`.
		"""
		options = Glossary.formatsWriteOptions.get(self._session.outputFormat)
		if options is None:
			log.error(f"internal error: invalid format {self._session.outputFormat!r}")
			return
		optionsProp = Glossary.plugins[self._session.outputFormat].optionsProp
		history = FileHistory(
			join(histDir, f"write-options-{self._session.outputFormat}")
		)
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			list(options),
			ignore_case=True,
			match_middle=True,
			sentence=True,
		)
		while True:
			try:
				optName = self._prompt.prompt(
					2,
					"WriteOption: Name (ENTER if done)",
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
			default = self._session.writeOptions.get(optName)
			if default is None:
				default = options[optName]
			while True:
				if option.typ == "bool":
					try:
						valueNew = self._prompt.checkbox_prompt(
							3,
							f"WriteOption: {optName}",
							default=default,
						)
					except (KeyboardInterrupt, EOFError):
						break
					print(f"Set write-option: {optName} = {valueNew!r}")
					self._session.writeOptions[optName] = valueNew
					break
				try:
					value = self._prompt.prompt(
						3,
						f"WriteOption: {optName}",
						colon=" =",
						history=FileHistory(join(histDir, f"option-value-{optName}")),
						auto_suggest=AutoSuggestFromHistory(),
						default=str(default),
						completer=valueCompleter,
					)
				except (KeyboardInterrupt, EOFError):
					break
				if value == "" and option.typ != "str":  # noqa: PLC1901
					if optName in self._session.writeOptions:
						print(f"Unset write-option {optName!r}")
						del self._session.writeOptions[optName]
					break
				valueNew, ok = option.evaluate(value)
				if not ok or not option.validate(valueNew):
					log.error(
						f"Invalid write option value {optName}={value!r}"
						f" for format {self._session.outputFormat}",
					)
					continue
				print(f"Set write-option: {optName} = {valueNew!r}")
				self._session.writeOptions[optName] = valueNew
				break

	def resetReadOptions(self) -> None:
		"""Clear all read plugin options for the current session."""
		self._session.readOptions = {}

	def resetWriteOptions(self) -> None:
		"""Clear all write plugin options for the current session."""
		self._session.writeOptions = {}

	def askConfigValue(self, configKey: str, option: Option) -> str:
		"""Prompt for one global config key (checkbox for bool, line input otherwise)."""
		default = self.config.get(configKey, "")
		if option.typ == "bool":
			return str(
				self._prompt.checkbox_prompt(
					3,
					f"Config: {configKey}",
					default=bool(default),
				),
			)
		return self._prompt.prompt(
			3,
			f"Config: {configKey}",
			colon=" =",
			history=FileHistory(join(histDir, f"config-value-{configKey}")),
			auto_suggest=AutoSuggestFromHistory(),
			default=str(default),
			completer=self.getOptionValueCompleter(option),
		)

	def askConfig(self) -> None:
		"""Loop: pick a config key, then set or unset its value in ``self.config``."""
		configKeys = sorted(configDefDict)
		history = FileHistory(join(histDir, "config-key"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			configKeys,
			ignore_case=True,
			match_middle=True,
			sentence=True,
		)

		while True:
			try:
				configKey = self._prompt.prompt(
					2,
					"Config: Key (ENTER if done)",
					history=history,
					auto_suggest=auto_suggest,
					completer=completer,
				)
			except (KeyboardInterrupt, EOFError):
				return
			if not configKey:
				return
			option = configDefDict[configKey]
			while True:
				try:
					value = self.askConfigValue(configKey, option)
				except (KeyboardInterrupt, EOFError):
					break
				if value == "" and option.typ != "str":  # noqa: PLC1901
					if configKey in self.config:
						print(f"Unset config {configKey!r}")
						del self.config[configKey]
					break
				valueNew, ok = option.evaluate(value)
				if not ok or not option.validate(valueNew):
					log.error(
						f"Invalid config value {configKey}={value!r}",
					)
					continue
				print(f"Set config: {configKey} = {valueNew!r}")
				self.config[configKey] = valueNew
				break

	def showOptions(self) -> None:
		"""Print current read/write/convert options and ``self.config`` to stdout."""
		print(f"readOptions = {self._session.readOptions}")
		print(f"writeOptions = {self._session.writeOptions}")
		print(f"convertOptions = {self._session.convertOptions}")
		print(f"config = {self.config}")
		print()

	def setIndirect(self) -> None:
		"""Force indirect conversion mode (disable direct and sqlite flags)."""
		self._session.convertOptions["direct"] = False
		self._session.convertOptions["sqlite"] = None
		print("Switched to indirect mode")

	def setSQLite(self) -> None:
		"""Use SQLite-backed conversion path (clears direct mode)."""
		self._session.convertOptions["direct"] = None
		self._session.convertOptions["sqlite"] = True
		print("Switched to SQLite mode")

	def setNoProgressbar(self) -> None:
		"""Disable the tqdm (or legacy) progress bar for the next conversion."""
		self._session.glossarySetAttrs["progressbar"] = False
		print("Disabled progress bar")

	def setSort(self) -> None:
		"""Toggle whether entries are sorted during conversion."""
		try:
			value = self._prompt.checkbox_prompt(
				2,
				"Enable Sort",
				default=self._session.convertOptions.get("sort", False),
			)
		except (KeyboardInterrupt, EOFError):
			return
		self._session.convertOptions["sort"] = value

	def setSortKey(self) -> None:
		"""Set or clear the named sort key; may prompt to enable sorting if off."""
		completer = WordCompleter(
			[sk.name for sk in namedSortKeyList],
			ignore_case=False,
			match_middle=True,
			sentence=True,
		)
		default = self._session.convertOptions.get("sortKeyName", "")
		sortKeyName = self._prompt.prompt(
			2,
			"SortKey",
			history=FileHistory(join(histDir, "sort-key")),
			auto_suggest=AutoSuggestFromHistory(),
			default=default,
			completer=completer,
		)
		if not sortKeyName:
			if "sortKeyName" in self._session.convertOptions:
				del self._session.convertOptions["sortKeyName"]
			return

		if not lookupSortKey(sortKeyName):
			log.error(f"invalid {sortKeyName = }")
			return

		self._session.convertOptions["sortKeyName"] = sortKeyName

		if not self._session.convertOptions.get("sort"):
			self.setSort()

	def askFinalAction(self) -> str | None:
		"""Read one menu token: empty means convert now; unknown tokens are rejected."""
		history = FileHistory(join(histDir, "action"))
		auto_suggest = AutoSuggestFromHistory()
		completer = WordCompleter(
			list(self._finalActions),
			ignore_case=False,
			match_middle=True,
			sentence=True,
		)
		while True:
			action = self._prompt.prompt(
				1,
				"Select action (ENTER to convert)",
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

	def askFinalOptions(self) -> bool | str:
		"""
		Dispatch pre-conversion menu actions until user chooses to convert or quit.

		Returns ``True`` to run conversion, ``False`` on interrupt/error, or
		:const:`back` to re-enter paths and formats.
		"""
		while True:
			try:
				action = self.askFinalAction()
			except (KeyboardInterrupt, EOFError):
				return False
			except Exception:
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

	def getRunKeywordArgs(self) -> dict:
		"""
		Keyword arguments for :meth:`pyglossary.ui.ui_cmd.UI.run`.

		Merges the session with ``self.config``.
		"""
		return self._session.get_run_kwargs(self.config)

	def checkInputFormat(self, forceAsk: bool = False) -> None:
		"""Set ``session.inputFormat`` from detection or by prompting if needed."""
		if not forceAsk:
			try:
				inputArgs = Glossary.detectInputFormat(self._session.inputFilename)
			except Error:
				pass
			else:
				inputFormat = inputArgs.formatName
				self._session.inputFormat = inputFormat
				return
		self._session.inputFormat = self.askInputFormat()

	def checkOutputFormat(self, forceAsk: bool = False) -> None:
		"""Set ``session.outputFormat`` from detection or by prompting if needed."""
		if not forceAsk:
			try:
				outputArgs = Glossary.detectOutputFormat(
					filename=self._session.outputFilename,
					inputFilename=self._session.inputFilename,
				)
			except Error:
				pass
			else:
				self._session.outputFormat = outputArgs.formatName
				return
		self._session.outputFormat = self.askOutputFormat()

	def askFormats(self) -> None:
		"""Re-prompt for both input and output formats (menu action)."""
		self.checkInputFormat(forceAsk=True)
		self.checkOutputFormat(forceAsk=True)

	def askInputOutputAgain(self) -> None:
		"""Re-ask for all four: input path, input format, output path, output format."""
		self.askInputFile()
		self.checkInputFormat(forceAsk=True)
		self.askOutputFile()
		self.checkOutputFormat(forceAsk=True)

	def printNonInteractiveCommand(self) -> None:  # noqa: PLR0912
		"""
		Print a ``pyglossary`` CLI invocation equivalent to the current session.

		May mutate ``session.convertOptions`` (e.g. pop ``infoOverride``) like the
		original implementation when building flags.
		"""
		cmd = [
			ui_cmd.COMMAND,
			self._session.inputFilename,
			self._session.outputFilename,
			f"--read-format={self._session.inputFormat}",
			f"--write-format={self._session.outputFormat}",
		]

		if self._session.readOptions:
			optionsJson = json.dumps(self._session.readOptions, ensure_ascii=True)
			cmd += ["--json-read-options", optionsJson]

		if self._session.writeOptions:
			optionsJson = json.dumps(self._session.writeOptions, ensure_ascii=True)
			cmd += ["--json-write-options", optionsJson]

		if self.config:
			for key, value in self.config.items():
				if value is None:
					continue
				if value == self.savedConfig.get(key):
					continue
				option = configDefDict.get(key)
				if option is None:
					log.error(f"config key {key} was not found")
				if not option.hasFlag:
					log.error(f"config key {key} has no command line flag")
				flag = option.customFlag
				if not flag:
					flag = key.replace("_", "-")
				if option.typ == "bool":
					if not value:
						flag = f"no-{flag}"
					cmd.append(f"--{flag}")
				else:
					cmd.append(f"--{flag}={value}")

		if self._session.convertOptions:
			if "infoOverride" in self._session.convertOptions:
				infoOverride = self._session.convertOptions.pop("infoOverride")
				for key, value in infoOverride.items():
					flag = infoOverrideFlags.get(key)
					if not flag:
						log.error(f"unknown key {key} in infoOverride")
						continue
					cmd.append(f"--{flag}={value}")

			if "sortKeyName" in self._session.convertOptions:
				value = self._session.convertOptions.pop("sortKeyName")
				cmd.append(f"--sort-key={value}")

			for key, value in self._session.convertOptions.items():
				if value is None:
					continue
				if key not in convertOptionsFlags:
					log.error(f"unknown key {key} in convertOptions")
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

		if (
			"progressbar" in self._session.glossarySetAttrs
			and not self._session.glossarySetAttrs["progressbar"]
		):
			cmd.append("--no-progress-bar")

		print()
		print(
			"If you want to repeat this conversion later, you can use this command:",
		)
		# shlex.join is added in Python 3.8
		print(shlex.join(cmd))

	def setConfigAttrs(self) -> None:
		"""Refresh prompt appearance from ``self.config`` (``cmdi.*`` keys)."""
		self._prompt.apply_config(self.config)

	# PLR0912 Too many branches (19 > 12)
	def main(self, again: bool = False) -> None:  # noqa: PLR0912
		"""
		Collect missing paths and formats, then loop: menu, convert, repeat until
		success or quit.

		Returns ``True``/falsy from the base ``run`` on success, or ``None`` if the
		user aborts during prompts.
		"""
		if again or not self._session.inputFilename:
			try:
				self.askInputFile()
			except (KeyboardInterrupt, EOFError):
				return None
		if again or not self._session.inputFormat:
			try:
				self.checkInputFormat()
			except (KeyboardInterrupt, EOFError):
				return None
		if again or not self._session.outputFilename:
			try:
				self.askOutputFile()
			except (KeyboardInterrupt, EOFError):
				return None
		if again or not self._session.outputFormat:
			try:
				self.checkOutputFormat()
			except (KeyboardInterrupt, EOFError):
				return None

		while True:
			status = self.askFinalOptions()
			if status == back:
				self.askInputOutputAgain()
				continue
			if not status:
				return None
			try:
				succeed = ui_cmd.UI.run(self, **self.getRunKeywordArgs())
			except Exception:
				log.exception("")
			else:
				self.printNonInteractiveCommand()
				if succeed:
					return succeed
			print("Press Control + C to exit")

	def run(  # noqa: PLR0913
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		config: ConfigType | None = None,
		readOptions: dict[str, Any] | None = None,
		writeOptions: dict[str, Any] | None = None,
		convertOptions: dict[str, Any] | None = None,
		glossarySetAttrs: dict[str, Any] | None = None,
	) -> bool:
		"""
		Load config, fill the session from arguments, run :meth:`main`, then exit loop.

		Unlike the base :meth:`pyglossary.ui.ui_cmd.UI.run`, this implementation
		keeps the process alive: user may convert again or save edited config.
		``reverse`` is not supported here.
		"""
		if reverse:
			raise NotImplementedError("Reverse is not implemented in this UI")

		self._session.inputFilename = inputFilename
		self._session.outputFilename = outputFilename
		self._session.inputFormat = inputFormat
		self._session.outputFormat = outputFormat
		self._session.readOptions = readOptions or {}
		self._session.writeOptions = writeOptions or {}
		self._session.convertOptions = convertOptions or {}
		self._session.glossarySetAttrs = glossarySetAttrs or {}

		if not self._progressbar:
			self._session.glossarySetAttrs["progressbar"] = False

		self.loadConfig()
		self.savedConfig = self.config.copy()
		self.config = config or {}

		del inputFilename, outputFilename, inputFormat, outputFormat
		del config, readOptions, writeOptions, convertOptions

		self.setConfigAttrs()

		self.main()

		try:
			while (
				self._prompt.prompt(
					level=1,
					msg="Press enter to exit, 'a' to convert again",
					default="",
				)
				== "a"
			):
				self.main(again=True)
		except KeyboardInterrupt:
			pass

		if self.config != self.savedConfig and confirm("Save Config?"):
			self.saveConfig()

		return True
