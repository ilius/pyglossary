# -*- coding: utf-8 -*-
# mypy: ignore-errors
# ui_cmd.py
#
# Copyright © 2008-2021 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import os
import sys
from os.path import join
from typing import TYPE_CHECKING, Any

from pyglossary.core import dataDir, log
from pyglossary.glossary_v2 import ConvertArgs, Error, Glossary

from .base import UIBase, fread
from .wcwidth import wcswidth

if TYPE_CHECKING:
	import logging
	from collections.abc import Mapping

__all__ = ["COMMAND", "UI", "parseFormatOptionsStr", "printHelp"]


def wc_ljust(text: str, length: int, padding: str = " ") -> str:
	return text + padding * max(0, (length - wcswidth(text)))


if os.sep == "\\":  # Operating system is Windows
	startBold = ""
	startUnderline = ""
	endFormat = ""
else:
	startBold = "\x1b[1m"  # Start Bold # len=4
	startUnderline = "\x1b[4m"  # Start Underline # len=4
	endFormat = "\x1b[0;0;0m"  # End Format # len=8
	# redOnGray = "\x1b[0;1;31;47m"


COMMAND = "pyglossary"


def getColWidth(subject: str, strings: list[str]) -> int:
	return max(len(x) for x in [subject] + strings)


def getFormatsTable(names: list[str], header: str) -> str:
	descriptions = [Glossary.plugins[name].description for name in names]
	extensions = [" ".join(Glossary.plugins[name].extensions) for name in names]

	nameWidth = getColWidth("Name", names)
	descriptionWidth = getColWidth("Description", descriptions)
	extensionsWidth = getColWidth("Extensions", extensions)

	lines = [
		"\n",
		startBold + header + endFormat,
		" | ".join(
			[
				"Name".center(nameWidth),
				"Description".center(descriptionWidth),
				"Extensions".center(extensionsWidth),
			],
		),
		"-+-".join(
			[
				"-" * nameWidth,
				"-" * descriptionWidth,
				"-" * extensionsWidth,
			],
		),
	]
	for index, name in enumerate(names):
		lines.append(
			" | ".join(
				[
					name.ljust(nameWidth),
					descriptions[index].ljust(descriptionWidth),
					extensions[index].ljust(extensionsWidth),
				],
			),
		)

	return "\n".join(lines)


def printHelp() -> None:
	import string

	text = fread(join(dataDir, "help"))
	text = (
		text.replace("<b>", startBold)
		.replace("<u>", startUnderline)
		.replace("</b>", endFormat)
		.replace("</u>", endFormat)
	)
	text = string.Template(text).substitute(
		CMD=COMMAND,
	)
	text += getFormatsTable(Glossary.readFormats, "Supported input formats:")
	text += getFormatsTable(Glossary.writeFormats, "Supported output formats:")
	print(text)


# TODO: raise exception instead of returning None
def parseFormatOptionsStr(st: str) -> dict[str, str] | None:
	"""Prints error and returns None if failed to parse one option."""
	st = st.strip()
	if not st:
		return {}

	opt: dict[str, str] = {}
	parts = st.split(";")
	for part in parts:
		if not part:
			continue
		eq = part.find("=")
		if eq < 1:
			log.critical(f"bad option syntax: {part!r}")
			return None
		key = part[:eq].strip()
		if not key:
			log.critical(f"bad option syntax: {part!r}")
			return None
		value = part[eq + 1 :].strip()
		opt[key] = value
	return opt


class NullObj:
	def __getattr__(self, attr: str) -> NullObj:
		return self

	def __setattr__(self, attr: str, value: Any) -> None:
		pass

	def __setitem__(self, key: str, value: Any) -> None:
		pass

	def __call__(
		self,
		*args: tuple[Any],
		**kwargs: Mapping[Any],
	) -> None:
		pass


class UI(UIBase):
	def __init__(
		self,
		progressbar: bool = True,
	) -> None:
		UIBase.__init__(self)
		# log.debug(self.config)
		self.pbar = NullObj()
		self._toPause = False
		self._resetLogFormatter = None
		self._progressbar = progressbar

	def onSigInt(
		self,
		*_args: tuple[Any],
	) -> None:
		log.info("")
		if self._toPause:
			log.info("Operation Canceled")
			sys.exit(0)
		else:
			self._toPause = True
			log.info("Please wait...")

	def setText(self, text: str) -> None:
		self.pbar.widgets[0] = text

	def fixLogger(self) -> None:
		for h in log.handlers:
			if h.name == "std":
				self.fixLogHandler(h)
				return

	def fillMessage(self, msg: str) -> str:
		term_width = self.pbar.term_width
		if term_width is None:
			# FIXME: why?
			return msg
		return "\r" + wc_ljust(msg, term_width)

	def fixLogHandler(self, h: logging.Handler) -> None:
		def reset() -> None:
			h.formatter.fill = None

		self._resetLogFormatter = reset
		h.formatter.fill = self.fillMessage

	def progressInit(self, title: str) -> None:
		try:
			from .pbar_tqdm import createProgressBar
		except ModuleNotFoundError:
			from .pbar_legacy import createProgressBar
		self.pbar = createProgressBar(title)
		self.fixLogger()

	def progress(
		self,
		ratio: float,
		text: str = "",  # noqa: ARG002
	) -> None:
		self.pbar.update(ratio)

	def progressEnd(self) -> None:
		self.pbar.finish()
		if self._resetLogFormatter:
			self._resetLogFormatter()

	def reverseLoop(
		self,
		*_args: tuple[Any],
		**kwargs: Mapping[Any],
	) -> None:
		from pyglossary.reverse import reverseGlossary

		reverseKwArgs: dict[str, Any] = {}
		for key in (
			"words",
			"matchWord",
			"showRel",
			"includeDefs",
			"reportStep",
			"saveStep",
			"maxNum",
			"minRel",
			"minWordLen",
		):
			try:
				reverseKwArgs[key] = self.config["reverse_" + key]
			except KeyError:
				pass
		reverseKwArgs.update(kwargs)

		if not self._toPause:
			log.info("Reversing glossary... (Press Ctrl+C to pause/stop)")
		for _ in reverseGlossary(self.glos, **reverseKwArgs):
			if self._toPause:
				log.info(
					"Reverse is paused. Press Enter to continue, and Ctrl+C to exit",
				)
				input()
				self._toPause = False

	# PLR0912 Too many branches (19 > 12)
	def run(  # noqa: PLR0912, PLR0913
		self,
		inputFilename: str = "",
		outputFilename: str = "",
		inputFormat: str = "",
		outputFormat: str = "",
		reverse: bool = False,
		config: dict[str, Any] | None = None,
		readOptions: dict[str, Any] | None = None,
		writeOptions: dict[str, Any] | None = None,
		convertOptions: dict[str, Any] | None = None,
		glossarySetAttrs: dict[str, Any] | None = None,
	) -> bool:
		if config is None:
			config = {}
		if readOptions is None:
			readOptions = {}
		if writeOptions is None:
			writeOptions = {}
		if convertOptions is None:
			convertOptions = {}
		if glossarySetAttrs is None:
			glossarySetAttrs = {}

		self.config = config

		if inputFormat:  # noqa: SIM102
			# inputFormat = inputFormat.capitalize()
			if inputFormat not in Glossary.readFormats:
				log.error(f"invalid read format {inputFormat}")
		if outputFormat:  # noqa: SIM102
			# outputFormat = outputFormat.capitalize()
			if outputFormat not in Glossary.writeFormats:
				log.error(f"invalid write format {outputFormat}")
				log.error(f"try: {COMMAND} --help")
				return False
		if not outputFilename:
			if reverse:
				pass
			elif outputFormat:
				try:
					ext = Glossary.plugins[outputFormat].extensions[0]
				except (KeyError, IndexError):
					log.error(f"invalid write format {outputFormat}")
					log.error(f"try: {COMMAND} --help")
					return False
				outputFilename = os.path.splitext(inputFilename)[0] + ext
			else:
				log.error("neither output file nor output format is given")
				log.error(f"try: {COMMAND} --help")
				return False

		glos = self.glos = Glossary(ui=self)
		glos.config = self.config
		glos.progressbar = self._progressbar

		for attr, value in glossarySetAttrs.items():
			setattr(glos, attr, value)

		if reverse:
			import signal

			signal.signal(signal.SIGINT, self.onSigInt)  # good place? FIXME
			readOptions["direct"] = True
			if not glos.read(
				inputFilename,
				formatName=inputFormat,
				**readOptions,
			):
				log.error("reading input file was failed!")
				return False
			self.setText("Reversing: ")
			self.pbar.update_step = 0.1
			self.reverseLoop(savePath=outputFilename)
			return True

		try:
			finalOutputFile = self.glos.convert(
				ConvertArgs(
					inputFilename,
					inputFormat=inputFormat,
					outputFilename=outputFilename,
					outputFormat=outputFormat,
					readOptions=readOptions,
					writeOptions=writeOptions,
					**convertOptions,
				),
			)
		except Error as e:
			log.critical(str(e))
			glos.cleanup()
			return False
		return bool(finalOutputFile)
