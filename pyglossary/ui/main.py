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

import argparse
import json
import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Callable

	from pyglossary.option import Option


from pyglossary import core  # essential
from pyglossary.langs import langDict
from pyglossary.sort_keys import lookupSortKey, namedSortKeyList
from pyglossary.ui.base import UIBase

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

log = None

ui_list = ["gtk", "tk"]
if os.sep == "\\":
	ui_list = ["tk", "gtk"]


def canRunGUI() -> bool:
	if core.sysName == "linux":
		return bool(os.getenv("DISPLAY"))

	if core.sysName == "darwin":
		try:
			import tkinter  # noqa: F401
		except ModuleNotFoundError:
			return False

	return True


class StoreConstAction(argparse.Action):
	def __init__(
		self,
		option_strings: "list[str]",
		same_dest: str = "",
		const_value: "bool | None" = None,
		nargs: int = 0,
		**kwargs,
	) -> None:
		if isinstance(option_strings, str):
			option_strings = [option_strings]
		argparse.Action.__init__(
			self,
			option_strings=option_strings,
			nargs=nargs,
			**kwargs,
		)
		self.same_dest = same_dest
		self.const_value = const_value

	def __call__(
		self,
		parser: "argparse.ArgumentParser | None" = None,
		namespace: "argparse.Namespace | None" = None,
		values: "list" = None,
		option_strings: "list[str]" = None,
		required: bool = False,
		dest: "str | None" = None,
	) -> "StoreConstAction":
		if not parser:
			return self
		dest = self.dest
		if getattr(namespace, dest) is not None:
			flag = self.option_strings[0]
			if getattr(namespace, dest) == self.const_value:
				parser.error(f"multiple {flag} options")
			else:
				parser.error(f"conflicting options: {self.same_dest} and {flag}")
		setattr(namespace, dest, self.const_value)
		return self


def registerConfigOption(
	parser: "argparse.ArgumentParser",
	key: str,
	option: "Option",
) -> None:
	if not option.hasFlag:
		return
	flag = option.customFlag
	if not flag:
		flag = key.replace('_', '-')

	if option.typ != "bool":
		parser.add_argument(
			f"--{flag}",
			dest=key,
			default=None,
			help=option.comment,
		)
		return

	if not option.comment:
		print(f"registerConfigOption: option has no comment: {option}")
		return

	if not option.falseComment:
		parser.add_argument(
			f"--{flag}",
			dest=key,
			action="store_true",
			default=None,
			help=option.comment,
		)
		return

	parser.add_argument(
		dest=key,
		action=StoreConstAction(
			f"--{flag}",
			same_dest=f"--no-{flag}",
			const_value=True,
			dest=key,
			default=None,
			help=option.comment,
		),
	)
	parser.add_argument(
		dest=key,
		action=StoreConstAction(
			f"--no-{flag}",
			same_dest=f"--{flag}",
			const_value=False,
			dest=key,
			default=None,
			help=option.falseComment,
		),
	)


def base_ui_run(
	inputFilename: str = "",
	outputFilename: str = "",
	inputFormat: str = "",
	outputFormat: str = "",
	reverse: bool = False,
	config: "dict | None" = None,
	readOptions: "dict | None" = None,
	writeOptions: "dict | None" = None,
	convertOptions: "dict | None" = None,
	glossarySetAttrs: "dict | None" = None,
) -> bool:
	from pyglossary.glossary_v2 import ConvertArgs, Glossary
	if reverse:
		log.error("--reverse does not work with --ui=none")
		return False
	ui = UIBase()
	ui.loadConfig(**config)
	glos = Glossary(ui=ui)
	glos.config = ui.config
	if glossarySetAttrs:
		for attr, value in glossarySetAttrs.items():
			setattr(glos, attr, value)
	glos.convert(ConvertArgs(
		inputFilename=inputFilename,
		outputFilename=outputFilename,
		inputFormat=inputFormat,
		outputFormat=outputFormat,
		readOptions=readOptions,
		writeOptions=writeOptions,
		**convertOptions,
	))
	return True


def getGitVersion(gitDir: str) -> str:
	import subprocess
	try:
		outputB, _err = subprocess.Popen(
			[
				"git",
				"--git-dir", gitDir,
				"describe",
				"--always",
			],
			stdout=subprocess.PIPE,
		).communicate()
	except Exception as e:
		sys.stderr.write(str(e) + "\n")
		return ""
	# if _err is None:
	return outputB.decode("utf-8").strip()


def getVersion() -> str:
	from pyglossary.core import rootDir
	gitDir = os.path.join(rootDir, ".git")
	if os.path.isdir(gitDir):
		version = getGitVersion(gitDir)
		if version:
			return version
	return core.VERSION


def validateLangStr(st: str) -> "str | None":
	lang = langDict[st]
	if lang:
		return lang.name
	lang = langDict[st.lower()]
	if lang:
		return lang.name
	log.error(f"unknown language {st!r}")
	return None


def shouldUseCMD(args: "argparse.Namespace") -> bool:
	if not canRunGUI():
		return True
	if args.interactive:
		return True
	if args.inputFilename and args.outputFilename:
		return True
	return False


def getRunner(args: "argparse.Namespace", ui_type: str) -> "Callable":
	if ui_type == "none":
		return base_ui_run

	if ui_type == "auto" and shouldUseCMD(args):
		ui_type = "cmd"

	uiArgs = {
		"progressbar": args.progressbar is not False,
	}

	if ui_type == "cmd":
		if args.interactive:
			from pyglossary.ui.ui_cmd_interactive import UI
		elif args.inputFilename and args.outputFilename:
			from pyglossary.ui.ui_cmd import UI
		elif not args.no_interactive:
			from pyglossary.ui.ui_cmd_interactive import UI
		else:
			log.error("no input file given, try --help")
			sys.exit(1)
		return UI(**uiArgs).run

	if ui_type == "auto":
		for ui_type2 in ui_list:
			try:
				ui_module = __import__(
					f"pyglossary.ui.ui_{ui_type2}",
					fromlist=f"ui_{ui_type2}",
				)
			except ImportError as e:
				log.error(str(e))
			else:
				return ui_module.UI(**uiArgs).run
		log.error(
			"no user interface module found! "
			f"try \"{sys.argv[0]} -h\" to see command line usage",
		)
		sys.exit(1)

	ui_module = __import__(
		f"pyglossary.ui.ui_{ui_type}",
		fromlist=f"ui_{ui_type}",
	)
	return ui_module.UI(**uiArgs).run


def main() -> None:
	global log

	uiBase = UIBase()
	uiBase.loadConfig()
	config = uiBase.config
	defaultHasColor = config.get(
		"color.enable.cmd.windows" if os.sep == "\\"
		else "color.enable.cmd.unix",
		True,
	)

	parser = argparse.ArgumentParser(
		prog=sys.argv[0],
		add_help=False,
		# allow_abbrev=False,
	)

	parser.add_argument(
		"-v",
		"--verbosity",
		action="store",
		dest="verbosity",
		type=int,
		choices=(0, 1, 2, 3, 4, 5),
		required=False,
		default=int(os.getenv("VERBOSITY", "3")),
	)

	parser.add_argument(
		"--version",
		action="store_true",
	)
	parser.add_argument(
		"-h",
		"--help",
		dest="help",
		action="store_true",
	)
	parser.add_argument(
		"-u",
		"--ui",
		dest="ui_type",
		default="auto",
		choices=(
			"cmd",
			"gtk",
			"gtk4",
			"tk",
			# "qt",
			"auto",
			"none",
		),
	)
	parser.add_argument(
		"--cmd",
		dest="ui_type",
		action="store_const",
		const="cmd",
		default=None,
		help="use command-line user interface",
	)
	parser.add_argument(
		"--gtk",
		dest="ui_type",
		action="store_const",
		const="gtk",
		default=None,
		help="use Gtk-based user interface",
	)
	parser.add_argument(
		"--gtk4",
		dest="ui_type",
		action="store_const",
		const="gtk4",
		default=None,
		help="use Gtk4-based user interface",
	)
	parser.add_argument(
		"--tk",
		dest="ui_type",
		action="store_const",
		const="tk",
		default=None,
		help="use Tkinter-based user interface",
	)
	parser.add_argument(
		"--interactive",
		"--inter",
		dest="interactive",
		action="store_true",
		default=None,
		help="switch to interactive command line interface",
	)
	parser.add_argument(
		"--no-interactive",
		"--no-inter",
		dest="no_interactive",
		action="store_true",
		default=None,
		help=(
			"do not automatically switch to interactive command line"
			" interface, for scripts"
		),
	)

	parser.add_argument(
		"-r",
		"--read-options",
		dest="readOptions",
		default="",
	)
	parser.add_argument(
		"-w",
		"--write-options",
		dest="writeOptions",
		default="",
	)

	parser.add_argument(
		"--json-read-options",
		dest="jsonReadOptions",
		default=None,
	)
	parser.add_argument(
		"--json-write-options",
		dest="jsonWriteOptions",
		default=None,
	)

	parser.add_argument(
		"--read-format",
		dest="inputFormat",
	)
	parser.add_argument(
		"--write-format",
		dest="outputFormat",
		action="store",
	)

	parser.add_argument(
		"--direct",
		dest="direct",
		action="store_true",
		default=None,
		help="if possible, convert directly without loading into memory",
	)
	parser.add_argument(
		"--indirect",
		dest="direct",
		action="store_false",
		default=None,
		help=(
			"disable `direct` mode, load full data into memory before writing"
			", this is default"
		),
	)
	parser.add_argument(
		"--sqlite",
		dest="sqlite",
		action="store_true",
		default=None,
		help=(
			"use SQLite as middle storage instead of RAM in direct mode,"
			"for very large glossaries"
		),
	)
	parser.add_argument(
		"--no-sqlite",
		dest="sqlite",
		action="store_false",
		default=None,
		help="do not use SQLite mode",
	)

	parser.add_argument(
		"--no-progress-bar",
		dest="progressbar",
		action="store_false",
		default=None,
	)
	parser.add_argument(
		"--no-color",
		dest="noColor",
		action="store_true",
		default=not defaultHasColor,
	)

	parser.add_argument(
		"--sort",
		dest="sort",
		action="store_true",
		default=None,
	)
	parser.add_argument(
		"--no-sort",
		dest="sort",
		action="store_false",
		default=None,
	)
	parser.add_argument(
		"--sort-key",
		action="store",
		dest="sortKeyName",
		default=None,
		help="name of sort key",
	)
	parser.add_argument(
		"--sort-encoding",
		action="store",
		dest="sortEncoding",
		default=None,
		help="encoding of sort (default utf-8)",
	)

	# _______________________________

	parser.add_argument(
		"--source-lang",
		action="store",
		dest="sourceLang",
		default=None,
		help="source/query language",
	)
	parser.add_argument(
		"--target-lang",
		action="store",
		dest="targetLang",
		default=None,
		help="target/definition language",
	)
	parser.add_argument(
		"--name",
		action="store",
		dest="name",
		default=None,
		help="glossary name/title",
	)

	# _______________________________

	parser.add_argument(
		"--reverse",
		dest="reverse",
		action="store_true",
	)

	parser.add_argument(
		"inputFilename",
		action="store",
		default="",
		nargs="?",
	)
	parser.add_argument(
		"outputFilename",
		action="store",
		default="",
		nargs="?",
	)

	# _______________________________

	for key, option in UIBase.configDefDict.items():
		registerConfigOption(parser, key, option)

	# _______________________________

	args = parser.parse_args()

	# parser.conflict_handler == "error"

	if args.version:
		print(f"PyGlossary {getVersion()}")
		sys.exit(0)

	log = logging.getLogger("pyglossary")

	ui_type = args.ui_type
	if ui_type == "none":
		args.noColor = True

	core.noColor = args.noColor
	logHandler = core.StdLogHandler(
		noColor=args.noColor,
	)
	log.setVerbosity(args.verbosity)
	log.addHandler(logHandler)
	# with the logger set up, we can import other pyglossary modules, so they
	# can do some logging in right way.

	for param1, param2 in UIBase.conflictingParams:
		if getattr(args, param1) and getattr(args, param2):
			log.critical(
				"Conflicting flags: "
				f"--{param1.replace('_', '-')} and "
				f"--{param2.replace('_', '-')}",
			)
			sys.exit(1)

	if args.sqlite:
		# args.direct is None by default which means automatic
		args.direct = False

	if not args.sort:
		if args.sortKeyName:
			log.critical("Passed --sort-key without --sort")
			sys.exit(1)
		if args.sortEncoding:
			log.critical("Passed --sort-encoding without --sort")
			sys.exit(1)

	if args.sortKeyName and not lookupSortKey(args.sortKeyName):
		_valuesStr = ", ".join(_sk.name for _sk in namedSortKeyList)
		log.critical(
			f"Invalid sortKeyName={args.sortKeyName!r}"
			f". Supported values:\n{_valuesStr}",
		)
		sys.exit(1)

	core.checkCreateConfDir()

	if sys.getdefaultencoding() != "utf-8":
		log.warning(f"System encoding is not utf-8, it's {sys.getdefaultencoding()!r}")

	##############################

	from pyglossary.glossary_v2 import Glossary
	from pyglossary.ui.ui_cmd import parseFormatOptionsStr, printHelp

	Glossary.init()

	if core.isDebug():
		log.debug(f"en -> {langDict['en']!r}")

	##############################

	# log.info(f"PyGlossary {core.VERSION}")

	if args.help:
		printHelp()
		sys.exit(0)

	# only used in ui_cmd for now
	readOptions = parseFormatOptionsStr(args.readOptions)
	if readOptions is None:
		return
	if args.jsonReadOptions:
		newReadOptions = json.loads(args.jsonReadOptions)
		if isinstance(newReadOptions, dict):
			readOptions.update(newReadOptions)
		else:
			log.error(
				f"invalid value for --json-read-options, "
				f"must be an object/dict, not {type(newReadOptions)}",
			)

	writeOptions = parseFormatOptionsStr(args.writeOptions)
	if writeOptions is None:
		return
	if args.jsonWriteOptions:
		newWriteOptions = json.loads(args.jsonWriteOptions)
		if isinstance(newWriteOptions, dict):
			writeOptions.update(newWriteOptions)
		else:
			log.error(
				f"invalid value for --json-write-options, "
				f"must be an object/dict, not {type(newWriteOptions)}",
			)

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

	for key, option in uiBase.configDefDict.items():
		if not option.hasFlag:
			continue
		value = getattr(args, key, None)
		if value is None:
			continue
		log.debug(f"config: {key} = {value}")
		if not option.validate(value):
			log.error(f"invalid config value: {key} = {value!r}")
			continue
		config[key] = value

	logHandler.config = config

	convertOptions = {}
	for key in convertOptionsKeys:
		value = getattr(args, key, None)
		if value is not None:
			convertOptions[key] = value

	infoOverride = {}
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
		inputArgs = Glossary.detectInputFormat(
			args.inputFilename,
			format=args.inputFormat,
		)
		if not inputArgs:
			log.error(
				f"Could not detect format for input file {args.inputFilename}",
			)
			sys.exit(1)
		inputFormat = inputArgs.formatName
		readOptionsProp = Glossary.plugins[inputFormat].optionsProp
		for optName, optValue in readOptions.items():
			if optName not in Glossary.formatsReadOptions[inputFormat]:
				log.error(f"Invalid option name {optName} for format {inputFormat}")
				sys.exit(1)
			prop = readOptionsProp[optName]
			optValueNew, ok = prop.evaluate(optValue)
			if not ok or not prop.validate(optValueNew):
				log.error(
					f"Invalid option value {optName}={optValue!r}"
					f" for format {inputFormat}",
				)
				sys.exit(1)
			readOptions[optName] = optValueNew

	if args.outputFilename and writeOptions:
		outputArgs = Glossary.detectOutputFormat(
			filename=args.outputFilename,
			format=args.outputFormat,
			inputFilename=args.inputFilename,
		)
		if outputArgs is None:
			sys.exit(1)
		outputFormat = outputArgs.formatName
		writeOptionsProp = Glossary.plugins[outputFormat].optionsProp
		for optName, optValue in writeOptions.items():
			if optName not in Glossary.formatsWriteOptions[outputFormat]:
				log.error(f"Invalid option name {optName} for format {outputFormat}")
				sys.exit(1)
			prop = writeOptionsProp[optName]
			optValueNew, ok = prop.evaluate(optValue)
			if not ok or not prop.validate(optValueNew):
				log.error(
					f"Invalid option value {optName}={optValue!r}"
					f" for format {outputFormat}",
				)
				sys.exit(1)
			writeOptions[optName] = optValueNew

	if convertOptions:
		log.debug(f"{convertOptions = }")

	runKeywordArgs = {
		"inputFilename": args.inputFilename,
		"outputFilename": args.outputFilename,
		"inputFormat": args.inputFormat,
		"outputFormat": args.outputFormat,
		"reverse": args.reverse,
		"config": config,
		"readOptions": readOptions,
		"writeOptions": writeOptions,
		"convertOptions": convertOptions,
		"glossarySetAttrs": None,
	}

	run = getRunner(args, ui_type)
	try:
		ok = run(**runKeywordArgs)
	except KeyboardInterrupt:
		log.error("Cancelled")
		ok = False
	sys.exit(0 if ok else 1)
