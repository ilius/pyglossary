# -*- coding: utf-8 -*-
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

"""Colored prompts, line input, and embedded ``!`` filesystem commands."""

from __future__ import annotations

import argparse
import logging
import os
from os.path import (
	abspath,
	dirname,
	isabs,
	isdir,
	join,
)
from typing import TYPE_CHECKING, Any

from prompt_toolkit import ANSI
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import PromptSession

from pyglossary.core import noColor
from pyglossary.ui.terminal_theme import (
	ansi_fg_open_for_palette_code,
	hex_fg_for_palette_code,
	is_light_terminal_background,
)

from .checkbox import MiniCheckBoxPrompt
from .prompt import prompt

if TYPE_CHECKING:
	from prompt_toolkit.formatted_text import StyleAndTextTuples
	from prompt_toolkit.key_binding.key_processor import KeyPressEvent

__all__ = ["InteractivePrompt"]

log = logging.getLogger("pyglossary")

endFormat = "\x1b[0;0;0m"


class InteractivePrompt:
	"""
	Prompt styling, line input, boolean checkbox prompts, and ``!`` shell commands.

	Wraps ``prompt_toolkit`` for colored, indented prompts and offers mini
	commands (``!pwd``, ``!ls``, ``!cd``, ``!..``) while entering file paths.
	Call :meth:`apply_config` after loading PyGlossary config so ``cmdi.*`` keys
	control indent and colors.
	"""

	def __init__(self) -> None:
		"""Set default prompt appearance and register filesystem action handlers."""
		self.promptIndentStr = ">"
		self.promptIndentColor = 2
		self.promptMsgColor = -1
		self.msgColor = -1

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
			"Usage: !ls [--help] [-l] [FILE/DIRECTORY]...\n\n"
			"optional arguments:\n"
			"    --help      show this help message and exit\n"
			"    -l, --long  use a long listing format\n"
		)

		self.fs_actions: dict[str, tuple[Any, str]] = {
			"!pwd": (self.fs_pwd, ""),
			"!ls": (self.fs_ls, self.ls_usage),
			"!..": (self.fs_cd_parent, ""),
			"!cd": (self.fs_cd, ""),
		}

	def apply_config(self, config: dict[str, Any]) -> None:
		"""Apply ``cmdi.prompt.*`` and ``cmdi.msg.color`` from the active config dict."""
		self.promptIndentStr = config.get("cmdi.prompt.indent.str", ">")
		self.promptIndentColor = config.get("cmdi.prompt.indent.color", 2)
		self.promptMsgColor = config.get("cmdi.prompt.msg.color", -1)
		self.msgColor = config.get("cmdi.msg.color", -1)

	@staticmethod
	def fs_pwd(args: list[str]) -> None:
		"""Print working directory; warn if extra arguments are given."""
		if args:
			print(f"extra arguments: {args}")
		print(os.getcwd())

	@staticmethod
	def get_ls_l(
		arg: str,
		st: os.stat_result | None = None,
		parentDir: str = "",
		sizeWidth: int = 0,
	) -> str:
		"""
		Format one ``ls -l``-style line for ``arg``.

		Resolve under ``parentDir`` when it is non-empty.
		"""
		import grp
		import pwd
		import stat
		import time

		argPath = arg
		if parentDir:
			argPath = join(parentDir, arg)
		if st is None:
			st = os.lstat(argPath)
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

	def fs_ls(self, args: list[str]) -> None:
		"""List files like Unix ``ls``, supporting ``-l``/``--long`` and ``--help``."""
		opts, args = self.ls_parser.parse_known_args(args=args)

		if opts.help:
			print(self.ls_usage)
			return

		if not args:
			args = [os.getcwd()]

		showTitle = len(args) > 1

		for argI, arg in enumerate(args):
			if argI > 0:
				print()

			if not isdir(arg):
				print(self.get_ls_l(arg))
				continue

			if showTitle:
				print(f"> List of directory {arg!r}:")

			if not opts.long:
				for path in os.listdir(arg):
					if isdir(path):
						print(f"{path}/")
					else:
						print(f"{path}")
				continue

			contents = os.listdir(arg)
			statList = [os.lstat(join(arg, relPath)) for relPath in contents]
			maxFileSize = max(st.st_size for st in statList)
			sizeWidth = len(str(maxFileSize))
			for pathI, path_ in enumerate(contents):
				print(
					self.get_ls_l(
						path_,
						parentDir=arg,
						st=statList[pathI],
						sizeWidth=sizeWidth,
					),
				)

	@staticmethod
	def fs_cd_parent(args: list[str]) -> None:
		"""Change to the parent directory (``cd ..``)."""
		if args:
			log.error("This command does not take arguments")
			return
		newDir = dirname(os.getcwd())
		os.chdir(newDir)
		print(f"Changed current directory to: {newDir}")

	@staticmethod
	def fs_cd(args: list[str]) -> None:
		"""Change directory to the single argument (resolved to an absolute path)."""
		if len(args) != 1:
			log.error("This command takes exactly one argument")
			return
		newDir = args[0]
		if not isabs(newDir):
			newDir = abspath(newDir)
		os.chdir(newDir)
		print(f"Changed current directory to: {newDir}")

	def formatPromptMsg(
		self,
		level: int,
		msg: str,
		colon: str = ":",
	) -> tuple[str, bool]:
		"""Build a plain-string prompt prefix and whether ANSI coloring was applied."""
		indent_ = self.promptIndentStr * level

		if noColor:
			return f"{indent_} {msg}{colon} ", False

		light_bg = is_light_terminal_background()

		if self.promptIndentColor >= 0:
			indent_ = (
				f"{ansi_fg_open_for_palette_code(self.promptIndentColor, light_bg)}"
				f"{indent_}{endFormat}"
			)

		if self.promptMsgColor >= 0:
			msg = (
				f"{ansi_fg_open_for_palette_code(self.promptMsgColor, light_bg)}"
				f"{msg}{endFormat}"
			)

		return f"{indent_} {msg}{colon} ", True

	def formatPromptMsgStyleList(
		self,
		level: int,
		msg: str,
		colon: str = ":",
	) -> StyleAndTextTuples:
		"""Build prompt_toolkit style tuples for the same prompt (used by checkbox UI)."""
		indent_ = self.promptIndentStr * level
		if noColor:
			return [("", f"{indent_} {msg}{colon} ")]

		light_bg = is_light_terminal_background()

		indentStyle = ""
		if self.promptIndentColor >= 0:
			indentStyle = "fg:" + hex_fg_for_palette_code(
				self.promptIndentColor,
				light_bg,
			)

		msgStyle = ""
		if self.promptMsgColor >= 0:
			msgStyle = "fg:" + hex_fg_for_palette_code(self.promptMsgColor, light_bg)

		return [
			(indentStyle, f"{indent_} "),
			(msgStyle, msg),
			("", f"{colon} "),
		]

	def prompt(self, level: int, msg: str, colon: str = ":", **kwargs: Any) -> str:
		"""
		Read a line with optional history, completion, and default.

		Extra ``kwargs`` are forwarded to ``prompt_toolkit``.
		"""
		msg2, colored = self.formatPromptMsg(level, msg, colon)
		if colored:
			msg2 = ANSI(msg2)
		return prompt(msg2, **kwargs)

	def checkbox_prompt(
		self,
		level: int,
		msg: str,
		default: bool,
		colon: str = ":",
	) -> bool:
		"""Show ``[x]``/``[ ]`` and toggle with Space; return the final boolean."""
		bindings = KeyBindings()

		check = MiniCheckBoxPrompt(
			formatted=self.formatPromptMsgStyleList(level, msg, colon=colon),
			value=default,
		)

		@bindings.add(" ")
		def _space(_event: KeyPressEvent) -> None:
			check.value = not check.value

		@bindings.add(Keys.Any)
		def _(_event: KeyPressEvent) -> None:
			"""Disallow inserting other text."""

		complete_message = check
		session: PromptSession[bool] = PromptSession(
			complete_message,
			key_bindings=bindings,
		)
		session.prompt()
		return check.value
