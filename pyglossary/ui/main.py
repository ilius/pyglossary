# -*- coding: utf-8 -*-
# mypy: ignore-errors
# ui/main.py
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Any, cast

from pyglossary import core, logger  # essential
from pyglossary.langs import langDict
from pyglossary.ui.argparse_main import configFromArgs, defineFlags, validateFlags
from pyglossary.ui.base import UIBase

__all__ = ["main", "mainNoExit"]

# TODO: move to docs:
# examples for read and write options:
# --read-options testOption=stringValue
# --read-options enableFoo=True
# --read-options fooList=[1,2,3]
# --read-options 'fooList=[1, 2, 3]'
# --read-options 'testOption=stringValue; enableFoo=True; fooList=[1, 2, 3]'
# --read-options 'testOption=stringValue;enableFoo=True;fooList=[1,2,3]'

# if a desired value contains ";", you can use --json-read-options
# or --json-write-options flags instead, with json object as value,
# quoted for command line. for example:
# 	'--json-write-options={"delimiter": ";"}'


# the first thing to do is to set up logger.
# other modules also using logger "root", so it is essential to set it up prior
# to importing anything else; with exception to pyglossary.core which sets up
# logger class, and so should be done before actually initializing logger.
# verbosity level may be given on command line, so we have to parse arguments
# before setting up logger.
# once more:
# - import system modules like os, sys, argparse etc and pyglossary.core
# - parse args
# - set up logger
# - import submodules
# - other code

# no-progress-bar only for command line UI
# TODO: load ui-dependent available options from ui modules
# (for example ui_cmd.available_options)
# the only problem is that it has to "import gtk" before it get the
# "ui_gtk.available_options"

# TODO
# -v (verbose or version?)
# -r (reverse or read-options)

log: logger.Logger | None = None


def validateLangStr(st: str) -> str | None:
	lang = langDict[st]
	if lang:
		return lang.name
	lang = langDict[st.lower()]
	if lang:
		return lang.name
	assert log
	log.error(f"unknown language {st!r}")
	return None


convertOptionsKeys = (
	"direct",
	"sort",
	"sortKeyName",
	"sortEncoding",
	"sqlite",
)
infoOverrideSpec = (
	("sourceLang", validateLangStr),
	("targetLang", validateLangStr),
	("name", str),
)


@dataclass(slots=True, frozen=True)
class MainPrepareResult:
	args: argparse.Namespace
	uiType: str
	inputFilename: str
	outputFilename: str
	inputFormat: str | None
	outputFormat: str | None
	reverse: bool
	config: dict
	readOptions: dict[str, Any]
	writeOptions: dict[str, Any]
	convertOptions: dict[str, Any]


# TODO:
# PLR0911 Too many return statements (7 > 6)
# PLR0915 Too many statements (56 > 50)
def mainPrepare() -> tuple[bool, MainPrepareResult | None]:
	global log

	uiBase = UIBase()
	uiBase.loadConfig()
	config = uiBase.config

	parser = argparse.ArgumentParser(
		prog=sys.argv[0],
		add_help=False,
		# allow_abbrev=False,
	)

	defineFlags(parser, config)

	# _______________________________

	args = parser.parse_args()

	# parser.conflict_handler == "error"

	if args.version:
		from pyglossary.ui.version import getVersion

		print(f"PyGlossary {getVersion()}")
		return True, None

	log = cast("logger.Logger", logging.getLogger("pyglossary"))

	if args.ui_type == "none":
		args.noColor = True

	core.noColor = args.noColor
	logHandler = logger.StdLogHandler(
		noColor=args.noColor,
	)
	log.setVerbosity(args.verbosity)
	log.addHandler(logHandler)
	# with the logger set up, we can import other pyglossary modules, so they
	# can do some logging in right way.

	if not validateFlags(args, log):
		return False, None

	if args.sqlite:
		# args.direct is None by default which means automatic
		args.direct = False

	core.checkCreateConfDir()

	if sys.getdefaultencoding() != "utf-8":
		log.warning(f"System encoding is not utf-8, it's {sys.getdefaultencoding()!r}")

	##############################

	from pyglossary.glossary_v2 import Glossary
	from pyglossary.ui.ui_cmd import printHelp

	Glossary.init()

	if core.isDebug():
		log.debug(f"en -> {langDict['en']!r}")

	##############################

	# log.info(f"PyGlossary {core.VERSION}")

	if args.help:
		printHelp()
		return True, None

	from pyglossary.ui.option_ui import (
		evaluateReadOptions,
		evaluateWriteOptions,
		parseReadWriteOptions,
	)

	# only used in ui_cmd for now
	rwOpts, err = parseReadWriteOptions(args)
	if err:
		log.error(err)
	if rwOpts is None:
		return False, None
	readOptions, writeOptions = rwOpts

	config.update(configFromArgs(args, log))
	logHandler.config = config

	convertOptions: dict[str, Any] = {}
	for key in convertOptionsKeys:
		value = getattr(args, key, None)
		if value is not None:
			convertOptions[key] = value

	infoOverride: dict[str, str] = {}
	for key, validate in infoOverrideSpec:
		value = getattr(args, key, None)
		if value is None:
			continue
		value = validate(value)
		if value is None:
			continue
		infoOverride[key] = value
	if infoOverride:
		convertOptions["infoOverride"] = infoOverride

	if args.inputFilename and readOptions:
		readOptions, err = evaluateReadOptions(
			readOptions,
			args.inputFilename,
			args.inputFormat,
		)
		if err:
			log.error(err)
		if readOptions is None:
			return False, None

	if args.outputFilename and writeOptions:
		writeOptions, err = evaluateWriteOptions(
			writeOptions,
			args.inputFilename,
			args.outputFilename,
			args.outputFormat,
		)
		if err:
			log.error(err)
		if writeOptions is None:
			return False, None

	if convertOptions:
		log.debug(f"{convertOptions = }")

	return True, MainPrepareResult(
		args=args,
		uiType=args.ui_type,
		inputFilename=args.inputFilename,
		outputFilename=args.outputFilename,
		inputFormat=args.inputFormat,
		outputFormat=args.outputFormat,
		reverse=args.reverse,
		config=config,
		readOptions=readOptions,
		writeOptions=writeOptions,
		convertOptions=convertOptions,
	)


def mainNoExit() -> bool:  # noqa: PLR0912
	ok, res = mainPrepare()
	if not ok:
		return False
	if res is None:  # --version or --help
		return True

	from pyglossary.ui.runner import getRunner

	assert log
	run = getRunner(res.args, res.uiType, log)
	if run is None:
		return False

	try:
		return run(
			inputFilename=res.inputFilename,
			outputFilename=res.outputFilename,
			inputFormat=res.inputFormat,
			outputFormat=res.outputFormat,
			reverse=res.reverse,
			config=res.config,
			readOptions=res.readOptions,
			writeOptions=res.writeOptions,
			convertOptions=res.convertOptions,
			glossarySetAttrs=None,
		)
	except KeyboardInterrupt:
		log.error("Cancelled")
		return False


def main() -> None:
	sys.exit(int(not mainNoExit()))
