#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

import os
import sys
import argparse
import json
import logging

from pyglossary import core  # essential
from pyglossary.entry import Entry
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


def canRunGUI():
	if core.sysName == "linux":
		return bool(os.getenv("DISPLAY"))

	if core.sysName == "darwin":
		try:
			import tkinter
		except ModuleNotFoundError:
			return False

	return True


def registerOption(parser, key: str, option: "Option"):
	if not option.cmd:
		return
	flag = option.cmdFlag
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

	if option.comment:
		parser.add_argument(
			f"--{flag}",
			dest=key,
			action="store_true",
			default=None,
			help=option.comment,
		)

	if option.falseComment:
		parser.add_argument(
			f"--no-{flag}",
			dest=key,
			action="store_false",
			default=None,
			help=option.falseComment,
		)


def base_ui_run(
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
	from pyglossary.glossary import Glossary
	if reverse:
		log.error("--reverse does not work with --ui=none")
		return False
	ui = UIBase()
	ui.loadConfig(**configOptions)
	glos = Glossary(ui=ui)
	glos.config = ui.config
	if glossarySetAttrs:
		for attr, value in glossarySetAttrs.items():
			setattr(glos, attr, value)
	glos.convert(
		inputFilename=inputFilename,
		outputFilename=outputFilename,
		inputFormat=inputFormat,
		outputFormat=outputFormat,
		readOptions=readOptions,
		writeOptions=writeOptions,
		**convertOptions
	)
	return True


def getGitVersion(gitDir):
	import subprocess
	try:
		outputB, error = subprocess.Popen(
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
	# if error == None:
	return outputB.decode("utf-8").strip()


def getVersion():
	from pyglossary.core import rootDir
	gitDir = os.path.join(rootDir, ".git")
	if os.path.isdir(gitDir):
		version = getGitVersion(gitDir)
		if version:
			return version
	return core.VERSION


def main():
	parser = argparse.ArgumentParser(add_help=False)

	parser.add_argument(
		"-v",
		"--verbosity",
		action="store",
		dest="verbosity",
		type=int,
		choices=(0, 1, 2, 3, 4, 5),
		required=False,
		default=3,
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
		"--tk",
		dest="ui_type",
		action="store_const",
		const="tk",
		default=None,
		help="use Tkinter-based user interface",
	)
	parser.add_argument(
		"--interactive",
		dest="interactive",
		action="store_true",
		default=None,
		help="switch to interactive command line interface",
	)
	parser.add_argument(
		"--no-interactive",
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
		help="use SQLite as middle storage instead of RAM in direct mode, for very large glossaries",
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
		default=(os.sep != "/"),
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
		"--sort-cache-size",
		dest="sortCacheSize",
		type=int,
		default=None,
	)

	# _______________________________

	parser.add_argument(
		"--source-lang",
		action="store",
		dest="sourceLangName",
		default=None,
		help=(
			"source/query language"
			" (may be overridden by input glossary)"
		),
	)
	parser.add_argument(
		"--target-lang",
		action="store",
		dest="targetLangName",
		default=None,
		help=(
			"target/definition language"
			" (may be overridden by input glossary)"
		)
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

	def shouldUseCMD(args):
		if not canRunGUI():
			return True
		if args.interactive:
			return True
		if args.inputFilename and args.outputFilename:
			return True
		return False

	# _______________________________

	for key, option in UIBase.configDefDict.items():
		registerOption(parser, key, option)

	# _______________________________

	args = parser.parse_args()

	if args.version:
		print(f"PyGlossary {getVersion()}")
		sys.exit(0)

	log = logging.getLogger("pyglossary")

	ui_type = args.ui_type
	if ui_type == "none":
		args.noColor = True

	log.setVerbosity(args.verbosity)
	log.addHandler(
		core.StdLogHandler(noColor=args.noColor),
	)
	# with the logger setted up, we can import other pyglossary modules, so they
	# can do some logging in right way.

	if args.sqlite:
		if args.direct:
			log.critical("Conflicting flags: --sqlite and --direct")
			sys.exit(1)
		# args.direct is None by default which means automatic
		args.direct = False

	core.checkCreateConfDir()

	if sys.getdefaultencoding() != "utf-8":
		log.warn(f"System encoding is not utf-8, it's {sys.getdefaultencoding()!r}")

	##############################

	from pyglossary.glossary import Glossary, langDict
	from pyglossary.ui.ui_cmd import help, parseFormatOptionsStr

	Glossary.init()

	if log.isDebug():
		log.debug(f"en -> {langDict['en']!r}")

	##############################

	ui_list = [
		"gtk",
		"tk",
	]

	# log.info(f"PyGlossary {core.VERSION}")

	if args.help:
		help()
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
				f"must be an object/dict, not {type(newReadOptions)}"
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
				f"must be an object/dict, not {type(newWriteOptions)}"
			)

	"""
		examples for read and write options:
		--read-options testOption=stringValue
		--read-options enableFoo=True
		--read-options fooList=[1,2,3]
		--read-options 'fooList=[1, 2, 3]'
		--read-options 'testOption=stringValue; enableFoo=True; fooList=[1, 2, 3]'
		--read-options 'testOption=stringValue;enableFoo=True;fooList=[1,2,3]'

		if a desired value contains ";", you can use --json-read-options
		or --json-write-options flags instead, with json object as value,
		quoted for command line. for example:
			'--json-write-options={"delimiter": ";"}'

	"""

	convertOptionsKeys = (
		"direct",
		"progressbar",
		"sort",
		"sortCacheSize",
		# "sortKey",  # TODO
		"sqlite",
	)
	glossarySetAttrsNames = (
		"sourceLangName",
		"targetLangName",
		# "author",
	)

	config = {}
	for key, option in UIBase.configDefDict.items():
		if not option.cmd:
			continue
		value = getattr(args, key, None)
		if value is None:
			continue
		option = UIBase.configDefDict[key]
		if not option.validate(value):
			log.error("invalid config value: {key} = {value!r}")
			continue
		config[key] = value

	convertOptions = {}
	for key in convertOptionsKeys:
		value = getattr(args, key, None)
		if value is not None:
			convertOptions[key] = value

	if convertOptions.get("sort", False):
		convertOptions["defaultSortKey"] = Entry.defaultSortKey

	glossarySetAttrs = {}
	for key in glossarySetAttrsNames:
		value = getattr(args, key, None)
		if value is not None:
			glossarySetAttrs[key] = value

	if args.inputFilename and readOptions:
		inputArgs = Glossary.detectInputFormat(
			args.inputFilename,
			format=args.inputFormat,
		)
		if not inputArgs:
			log.error(
				f"Could not detect format for input file {args.inputFilename}"
			)
			sys.exit(1)
		inputFormat = inputArgs[1]
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
					f" for format {inputFormat}"
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
		_, outputFormat, _ = outputArgs
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
					f" for format {outputFormat}"
				)
				sys.exit(1)
			writeOptions[optName] = optValueNew

	if config:
		log.debug(f"config = {config}")
	if convertOptions:
		log.debug(f"convertOptions = {convertOptions}")
	if glossarySetAttrs:
		log.debug(f"glossarySetAttrs = {glossarySetAttrs}")

	runKeywordArgs = dict(
		inputFilename=args.inputFilename,
		outputFilename=args.outputFilename,
		inputFormat=args.inputFormat,
		outputFormat=args.outputFormat,
		reverse=args.reverse,
		configOptions=config,
		readOptions=readOptions,
		writeOptions=writeOptions,
		convertOptions=convertOptions,
		glossarySetAttrs=glossarySetAttrs,
	)

	if ui_type == "none":
		sys.exit(0 if base_ui_run(**runKeywordArgs) else 1)

	if ui_type == "auto" and shouldUseCMD(args):
		ui_type = "cmd"

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
		sys.exit(0 if UI().run(**runKeywordArgs) else 1)

	if ui_type == "auto":
		ui_module = None
		for ui_type2 in ui_list:
			try:
				ui_module = __import__(
					f"pyglossary.ui.ui_{ui_type2}",
					fromlist=f"ui_{ui_type2}",
				)
			except ImportError:
				log.exception("error while importing UI module:")
			else:
				break
		if ui_module is None:
			log.error(
				"no user interface module found! "
				f"try \"{sys.argv[0]} -h\" to see command line usage"
			)
			sys.exit(1)
	else:
		ui_module = __import__(
			f"pyglossary.ui.ui_{ui_type}",
			fromlist=f"ui_{ui_type}",
		)

	sys.exit(0 if ui_module.UI().run(**runKeywordArgs) else 1)
