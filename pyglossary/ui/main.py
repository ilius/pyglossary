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
import logging

from pyglossary import core  # essential
from pyglossary.entry import Entry

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
	if core.sysName == "Linux":
		return bool(os.getenv("DISPLAY"))

	if core.sysName == "Darwin":
		try:
			import tkinter
		except ModuleNotFoundError:
			return False

	return True


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
		"--log-time",
		dest="log_time",
		action="store_true",
		default=None,
	)
	parser.add_argument(
		"--no-log-time",
		dest="log_time",
		action="store_false",
		default=None,
	)

	parser.add_argument(
		"--version",
		action="version",
		version=f"PyGlossary {core.VERSION}",
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
		"--no-interactive",
		dest="no_interactive",
		action="store_true",
		default=None,
		help="do not automatically switch to interactive command line interface, for scripts",
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
		"--no-alts",
		dest="enable_alts",
		action="store_false",
		default=None,
		help="disable alternates",
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

	parser.add_argument(
		"--skip-resources",
		dest="skipResources",
		action="store_true",
		default=None,
		help="skip resources (images, audio, etc)",
	)
	parser.add_argument(
		"--utf8-check",
		dest="utf8Check",
		action="store_true",
		default=None,
	)
	parser.add_argument(
		"--no-utf8-check",
		dest="utf8Check",
		action="store_false",
		default=None,
	)
	parser.add_argument(
		"--lower",
		dest="lower",
		action="store_true",
		default=None,
		help="lowercase words before writing",
	)
	parser.add_argument(
		"--no-lower",
		dest="lower",
		action="store_false",
		default=None,
		help="do not lowercase words before writing",
	)
	parser.add_argument(
		"--remove-html",
		dest="remove_html",
		help="remove given html tags (comma-separated) from definitions",
	)
	parser.add_argument(
		"--remove-html-all",
		dest="remove_html_all",
		action="store_true",
		help="remove all html tags from definitions",
	)
	parser.add_argument(
		"--normalize-html",
		dest="normalize_html",
		action="store_true",
		help="lowercase and normalize html tags in definitions",
	)

	parser.add_argument(
		"--cleanup",
		dest="cleanup",
		action="store_true",
		default=None,
		help="cleanup cache or temporary files after convertion",
	)
	parser.add_argument(
		"--no-cleanup",
		dest="cleanup",
		action="store_false",
		default=None,
		help="do not cleanup cache or temporary files after convertion",
	)

	# _______________________________

	parser.add_argument(
		"--info",
		dest="save_info_json",
		action="store_true",
		help="save glossary info as json file with .info extension",
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

	args = parser.parse_args()

	log = logging.getLogger("pyglossary")

	defaultVerbosity = log.getVerbosity()

	log.setVerbosity(args.verbosity)
	log.addHandler(
		core.StdLogHandler(noColor=args.noColor),
	)
	# with the logger setted up, we can import other pyglossary modules, so they
	# can do some loggging in right way.

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
	writeOptions = parseFormatOptionsStr(args.writeOptions)
	if writeOptions is None:
		return

	"""
		examples for read and write options:
		--read-options testOption=stringValue
		--read-options enableFoo=True
		--read-options fooList=[1,2,3]
		--read-options 'fooList=[1, 2, 3]'
		--read-options 'testOption=stringValue; enableFoo=True; fooList=[1, 2, 3]'
		--read-options 'testOption=stringValue;enableFoo=True;fooList=[1,2,3]'
	"""

	configOptionsKeys = (
		# "verbosity",
		"utf8Check",
		"lower",
		"skipResources",
		"enable_alts",
		"remove_html",
		"remove_html_all",
		"normalize_html",
		"save_info_json",
		"log_time",
		"cleanup",
	)

	convertOptionsKeys = (
		"direct",
		"progressbar",
		"sort",
		"sortCacheSize",
		# "sortKey",  # TODO
	)

	configOptions = {}
	for param in configOptionsKeys:
		value = getattr(args, param, None)
		if value is not None:
			configOptions[param] = value

	convertOptions = {}
	for param in convertOptionsKeys:
		value = getattr(args, param, None)
		if value is not None:
			convertOptions[param] = value

	if convertOptions.get("sort", False):
		convertOptions["defaultSortKey"] = Entry.defaultSortKey

	if args.inputFilename and readOptions:
		inputFormat = Glossary.detectInputFormat(
			args.inputFilename,
			format=args.inputFormat,
		)
		if not inputFormat:
			log.error(
				f"Could not detect format for input file {args.inputFilename}"
			)
			sys.exit(1)
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
		_, outputFormat, _ = Glossary.detectOutputFormat(
			filename=args.outputFilename,
			format=args.outputFormat,
			inputFilename=args.inputFilename,
		)
		if not outputFormat:
			log.error(
				f"Could not detect format for output file {args.outputFilename}"
			)
			sys.exit(1)
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

	if configOptions:
		log.debug(f"configOptions = {configOptions}")
	if convertOptions:
		log.debug(f"convertOptions = {convertOptions}")

	"""
	ui_type: User interface type
	Possible values:
		cmd - Command line interface, this ui will automatically selected
			if you give both input and output file
		gtk - GTK interface
		tk - Tkinter interface
		qt - Qt interface
		auto - Use the first available UI
	"""
	ui_type = args.ui_type

	if ui_type == "auto":
		if not canRunGUI() or (args.inputFilename and args.outputFilename):
			ui_type = "cmd"

	if ui_type == "none":
		if args.reverse:
			log.error("--reverse does not work with --ui=none")
			sys.exit(1)
		glos = Glossary()
		glos.convert(
			args.inputFilename,
			inputFormat=args.inputFormat,
			outputFilename=args.outputFilename,
			outputFormat=args.outputFormat,
			readOptions=readOptions,
			writeOptions=writeOptions,
			**convertOptions
		)
		sys.exit(0)

	runKeywordArgs = dict(
		inputFilename=args.inputFilename,
		outputFilename=args.outputFilename,
		inputFormat=args.inputFormat,
		outputFormat=args.outputFormat,
		reverse=args.reverse,
		configOptions=configOptions,
		readOptions=readOptions,
		writeOptions=writeOptions,
		convertOptions=convertOptions,
	)

	if ui_type == "cmd":
		if args.inputFilename and args.outputFilename:
			from ui.ui_cmd import UI
		elif not args.no_interactive:
			from ui.ui_cmd_interactive import UI
		else:
			log.error("no input file given, try --help")
			sys.exit(1)
		sys.exit(0 if UI().run(**runKeywordArgs) else 1)

	if ui_type == "auto":
		ui_module = None
		for ui_type2 in ui_list:
			try:
				ui_module = getattr(
					__import__(f"ui.ui_{ui_type2}"),
					f"ui_{ui_type2}",
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
		ui_module = getattr(
			__import__(f"ui.ui_{ui_type}"),
			f"ui_{ui_type}",
		)

	sys.exit(0 if ui_module.UI(**configOptions).run(**runKeywordArgs) else 1)
